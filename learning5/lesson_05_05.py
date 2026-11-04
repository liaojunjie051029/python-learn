from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph


def reply_node(state: MessagesState):
    user_message = state["messages"][-1]

    return {
        "messages": [
            AIMessage(
                content=f"Node 已经收到你的问题：{user_message.content}"
            )
        ]
    }


builder = StateGraph(MessagesState)#创建一个空的流程图。

builder.add_node("reply", reply_node)#把 reply_node 注册进去。
#注意：这一步不会执行 reply_node，只是告诉 LangGraph：流程中有一个叫 reply 的步骤，它对应 Python 函数 reply_node。

# 这两条边暂时只是让流程可以运行,这两行是在描述顺序
# 开始
#   ↓
# reply_node
#   ↓
# 结束
builder.add_edge(START, "reply")
builder.add_edge("reply", END)

# builder    = 设计施工图
# compile    = 把施工图构建成可运行系统
# invoke     = 发送一次请求

graph = builder.compile()

result = graph.invoke(
    {
        "messages": [
            HumanMessage(content="我的订单还没有发货，可以退款吗？")
        ]
    }
)

for index, message in enumerate(result["messages"]):
    print(f"[{index}] {type(message).__name__}")
    print("内容:", message.content)