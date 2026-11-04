import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver
from dataclasses import dataclass
from langgraph.runtime import Runtime
from langgraph.store.memory import InMemoryStore

load_dotenv()

@dataclass
class Context:
    user_id: str


store = InMemoryStore()

store.put(
    ("U1001", "memories"),
    "preferred_channel",
    {
        "preferred_channel": "sms"
    },
)

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


# def call_model_node(state: MessagesState):#定义一个 Node。它接收当前 State。
#     print("进入 call_model_node")

#     ai_message = model_with_tools.invoke(#这对应你手写 Agent 中的一次模型调用。
#         state["messages"]
#     )

#     return {
#         "messages": [ai_message]#这个 Node 产生了一条新的 AIMessage，请把它加入 State。
#     }


def call_model_node(
    state: MessagesState,
    runtime: Runtime[Context],
):
    user_id = runtime.context.user_id
    namespace = (user_id, "memories")

    memories = runtime.store.search(namespace)#先从 Store 读取：

    print("当前用户:", user_id)
    print("读取到的长期记忆:", [item.value for item in memories])

    memory_lines = []

    for item in memories:
        for key, value in item.value.items():
            memory_lines.append(f"{key}: {value}")

    if memory_lines:
        memory_text = "\n".join(memory_lines)#然后转换成文本：
    else:
        memory_text = "暂无长期记忆"

    system_message = SystemMessage(#再创建一条临时的系统消息
        content=(
            "你是一个专业的 AI 客服。\n"
            "以下是用户的长期记忆，只有在问题相关时才使用：\n"
            f"{memory_text}\n"
            "不要把长期记忆当成客服知识库事实。"
        )
    )

    model_messages = [#最后传给模型
        system_message,
        *state["messages"],#*state["messages"] 的作用是把原来的消息列表展开到新列表中。
    ]

    ai_message = model_with_tools.invoke(model_messages)

    return {
        "messages": [ai_message]
    }

# builder = StateGraph(MessagesState)
builder = StateGraph(
    MessagesState,
    context_schema=Context,
)
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
# graph = builder.compile(checkpointer=checkpointer)

graph = builder.compile(
    checkpointer=checkpointer,
    store=store,
)

config = {
    "configurable": {
        "thread_id": "session-U1001-001"
    }
}

result = graph.invoke(
    {
        "messages": [
            HumanMessage(
                content="请根据我的长期记忆，告诉我我的通知偏好。"
            )
        ]
    },
    config,
    context=Context(user_id="U1001")
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

# result2 = graph.invoke(
#     {
#         "messages": [
#             HumanMessage(
#                 content="请再简短说一遍退款规则。"
#             )
#         ]
#     },
#     config,
#     context=Context(user_id="U1001")
# )

# snapshot2 = graph.get_state(config)

# print("第二次调用后的消息数量:", len(snapshot2.values["messages"]))
# print("第二次调用后的下一步节点:", snapshot2.next)


for index, message in enumerate(result["messages"]):
    print(f"\n[{index}] {type(message).__name__}")
    print("内容:", message.content)

    if getattr(message, "tool_calls", None):
        print("工具调用:", message.tool_calls)