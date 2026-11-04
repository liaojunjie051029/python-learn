from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool


@tool
def query_order_status(order_id: str) -> str:
    """查询指定订单的状态。"""
    return f"{order_id}: 已发货"


def main() -> None:
    print("工具名称:", query_order_status.name)
    print("工具描述:", query_order_status.description)
    print("工具参数:", query_order_status.args)

    # 这是测试模型，它不会访问 OpenAI，也不会消耗 API，而是按照预先准备好的列表依次返回结果：不访问真实 API，第一次调用返回第一个 AIMessage，第二次调用返回第二个。
    model = FakeMessagesListChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "query_order_status",
                        "args": {"order_id": "A1001"},
                        "id": "call_1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="订单 A1001 当前状态：已发货"),
        ]
    )

    messages = [
        SystemMessage(content="你是一个专业的 AI 客服。"),
        HumanMessage(content="帮我查询订单 A1001 的状态。"),
    ]

    ai_message = model.invoke(messages)
    messages.append(ai_message)

    print("模型请求的工具:", ai_message.tool_calls)

    for tool_call in ai_message.tool_calls:
        if tool_call["name"] != query_order_status.name:
            raise ValueError(f"未知工具: {tool_call['name']}")

        result = query_order_status.invoke(tool_call["args"])

        messages.append(
            ToolMessage(
                content=result,
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )

    final_message = model.invoke(messages)
    print("最终回答:", final_message.content)


if __name__ == "__main__":
    main()