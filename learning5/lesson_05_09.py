# TypedDict 用来描述 State 中有哪些字段，以及每个字段的类型。
# 它主要用于类型提示，不会在运行时创建一个真正的类实例。
from typing import TypedDict

# START 表示图的开始，END 表示图的结束。
# StateGraph 是 LangGraph 的流程图构建器。
from langgraph.graph import END, START, StateGraph
# RetryPolicy 是 Node 的自动重试策略。
from langgraph.types import RetryPolicy


class FAQState(TypedDict):
    # 用户的问题会在流程中一直携带着。
    question: str
    # 知识库查询成功后，Node 会把答案写入这个字段。
    answer: str


# 这个计数器只是为了模拟外部服务暂时失败。
# 真实项目中，失败次数通常来自网络异常、数据库连接异常或 API 超时，
# 不需要自己手动维护这样的计数器。
attempt_counter = {
    "count": 0
}


def retrieve_faq_node(state: FAQState):
    """模拟调用客服知识库的 Node。"""

    # 每进入一次 Node，就把模拟调用次数加 1。
    # 注意：RetryPolicy 会重新执行整个 Node 函数。
    attempt_counter["count"] += 1
    current_attempt = attempt_counter["count"]

    print(f"第 {current_attempt} 次调用客服知识库")

    # 前两次故意抛出异常，模拟 Qdrant、PostgreSQL 或外部 API 暂时不可用。
    # 抛出异常后，LangGraph 会根据 retry_policy 判断是否重新执行这个 Node。
    if current_attempt < 3:
        raise ConnectionError("模拟知识库暂时连接失败")

    # 第三次执行成功，返回对 State 的更新。
    # Node 不需要返回完整 State，只需要返回本次要更新的字段。
    return {
        "answer": "退款规则：未发货订单可以申请退款。"
    }


# 创建一个空的流程图，并声明这个图使用 FAQState 作为 State 结构。
builder = StateGraph(FAQState)

# 注册 retrieve_faq Node。
#
# retry_policy 的含义：
# - max_attempts=3：最多尝试 3 次，包含第一次执行；
# - initial_interval=0.1：第一次失败后等待 0.1 秒；
# - backoff_factor=1.0：后续等待时间乘以 1.0；
# - jitter=False：不加入随机延迟，方便学习和观察；
# - retry_on=ConnectionError：只有 ConnectionError 才自动重试。
#
# 生产环境中不要对所有异常都重试：参数错误、权限错误、退款重复提交等问题，
# 重试通常没有意义，甚至可能造成重复操作。
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
)

# 描述流程顺序：
# START → retrieve_faq → END
builder.add_edge(START, "retrieve_faq")
builder.add_edge("retrieve_faq", END)

# compile 会把 builder 中定义的 State、Node、Edge 和 RetryPolicy
# 组合成真正可以执行的 Graph。
graph = builder.compile()

# graph.invoke 是真正执行流程的地方。
# 这里传入的是初始 State，而不是普通函数参数。
result = graph.invoke(
    {
        "question": "未发货订单可以退款吗？",
        "answer": "",
    }
)

# Node 成功后返回的 answer 会被合并回 State，
# 所以最终结果中同时包含 question 和 answer。
print("最终 State:", result)
