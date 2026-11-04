import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()


@tool
def search_faq(question: str) -> str:
    """查询客服知识库中的常见问题。"""
    return "退款规则：未发货订单可以申请退款。"


model = ChatOpenAI(
    model=os.environ["OPENAI_MODEL"],
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_BASE_URL"],
)

model_with_tools = model.bind_tools([search_faq])


def call_model_node(state: MessagesState):#定义一个 Node。它接收当前 State。
    print("进入 call_model_node")

    ai_message = model_with_tools.invoke(#这对应你手写 Agent 中的一次模型调用。
        state["messages"]
    )

    return {
        "messages": [ai_message]#这个 Node 产生了一条新的 AIMessage，请把它加入 State。
    }


builder = StateGraph(MessagesState)
tool_node = ToolNode([search_faq])

builder.add_node("call_model", call_model_node)
builder.add_node("tools", tool_node)

# 暂时只让图执行一个模型节点
# builder.add_edge(START, "call_model")
# builder.add_edge("call_model", END)
builder.add_edge(START, "call_model")

def route_after_model(state: MessagesState):
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"

builder.add_conditional_edges(
    "call_model",
    route_after_model,
    {
        "tools": "tools",
        "end": END,
    },
)

builder.add_edge("tools", "call_model")

checkpointer = InMemorySaver()
# graph = builder.compile()
graph = builder.compile(checkpointer=checkpointer)

config = {
    "configurable": {
        "thread_id": "session-U1001-001"
    }
}

result = graph.invoke(
    {
        "messages": [
            HumanMessage(
                content="请查询客服知识库：我的订单还没有发货，可以退款吗？"
            )
        ]
    },
    config,
)


# result = graph.invoke(
#     {
#         "messages": [
#             HumanMessage(
#                 # content="请查询客服知识库：我的订单还没有发货，可以退款吗？"
#                 content="你好，请直接回复“你好”，不要调用任何工具。"
#             )
#         ]
#     }
# )


# ai_message = result["messages"][-1]

# tool_update = tool_node.invoke(
#     {
#         "messages": [ai_message]
#     }
# )

# print("\nToolNode 输出:")

# for message in tool_update["messages"]:
#     print("消息类型:", type(message).__name__)
#     print("内容:", message.content)
#     print("工具调用 ID:", message.tool_call_id)

# print("\n最终 State 中的消息：")

snapshot = graph.get_state(config)

print("保存的消息数量:", len(snapshot.values["messages"]))
print("下一步节点:", snapshot.next)

result2 = graph.invoke(
    {
        "messages": [
            HumanMessage(
                content="请再简短说一遍退款规则。"
            )
        ]
    },
    config,
)

snapshot2 = graph.get_state(config)

print("第二次调用后的消息数量:", len(snapshot2.values["messages"]))
print("第二次调用后的下一步节点:", snapshot2.next)


for index, message in enumerate(result["messages"]):
    print(f"\n[{index}] {type(message).__name__}")
    print("内容:", message.content)

    if getattr(message, "tool_calls", None):
        print("工具调用:", message.tool_calls)