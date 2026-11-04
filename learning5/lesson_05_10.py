from typing import TypedDict

from langgraph.errors import NodeError
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy


class FAQState(TypedDict):
    question: str
    answer: str


attempt_counter = {
    "count": 0
}


def retrieve_faq_node(state: FAQState):
    """模拟一个始终失败的客服知识库查询 Node。"""

    attempt_counter["count"] += 1
    print(f"第 {attempt_counter['count']} 次调用客服知识库")

    # 模拟 Qdrant 或 PostgreSQL 暂时不可用
    raise ConnectionError("客服知识库连接失败")


def faq_error_handler(
    state: FAQState,
    error: NodeError,
):
    """重试次数耗尽后的兜底处理函数。"""

    print(f"失败的 Node: {error.node}")
    print(f"最终错误: {error.error}")

    return {
        "answer": "客服知识库暂时不可用，请稍后重试，或转人工客服。"
    }


builder = StateGraph(FAQState)

builder.add_node(
    "retrieve_faq",
    retrieve_faq_node,
    retry_policy=RetryPolicy(
        max_attempts=3,
        initial_interval=0.1,
        backoff_factor=1.0,
        jitter=False,
        retry_on=ConnectionError,
    ),
    error_handler=faq_error_handler,
)

builder.add_edge(START, "retrieve_faq")
builder.add_edge("retrieve_faq", END)

graph = builder.compile()

result = graph.invoke(
    {
        "question": "未发货订单可以退款吗？",
        "answer": "",
    }
)

print("最终 State:", result)