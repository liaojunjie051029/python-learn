from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
)
from langgraph.graph import MessagesState, add_messages


class CustomerServiceState(MessagesState):
    user_id: str
    retrieved_docs: list[str]


state: CustomerServiceState = {
    "messages": [
        HumanMessage(content="我的订单还没有发货，可以退款吗？")
    ],
    "user_id": "U1001",
    "retrieved_docs": [],# 搜索结果
}

state["messages"] = add_messages(
    state["messages"],
    [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "search_faq",
                    "args": {"question": "未发货订单可以退款吗？"},
                    "id": "call_1",
                    "type": "tool_call",
                }
            ],
        )
    ],
)

state["messages"] = add_messages(
    state["messages"],
    [
        ToolMessage(
            content="退款规则：未发货订单可以申请退款。",
            tool_call_id="call_1",
        )
    ],
)

state["messages"] = add_messages(
    state["messages"],
    [
        AIMessage(content="未发货订单可以申请退款。")
    ],
)

for index, message in enumerate(state["messages"]):
    print(f"\n[{index}] {type(message).__name__}")
    print("内容:", message.content)

    if getattr(message, "tool_calls", None):
        print("工具调用:", message.tool_calls)

print("\n用户 ID:", state["user_id"])