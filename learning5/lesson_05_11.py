from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class RefundState(TypedDict):
    order_id: str
    status: str


def approval_node(state: RefundState):
    """
    在真正执行退款前，请人工审批。
    """

    decision = interrupt(
        {
            "action": "refund",
            "order_id": state["order_id"],
            "message": f"订单 {state['order_id']} 申请退款，是否批准？",
        }
# interrupt的作用是：
# 暂停 Graph
#   ↓
# Checkpoint 保存当前 State
#   ↓
# 把审批信息返回给调用方
#   ↓
# 等待人工决定
#   ↓
# 使用同一个 thread_id 恢复
# 官方当前写法是 interrupt() 暂停，用 Command(resume=...) 恢复
    )

    print("收到人工决定:", decision)

    if decision["approved"]:
        return Command(goto="execute_refund")

    return Command(goto="cancel_refund")


def execute_refund_node(state: RefundState):
    """
    模拟真正执行退款。
    """

    print(f"执行订单 {state['order_id']} 的退款操作")

    return {
        "status": "refunded"
    }


def cancel_refund_node(state: RefundState):
    """
    人工拒绝退款后的处理。
    """

    print(f"拒绝订单 {state['order_id']} 的退款申请")

    return {
        "status": "rejected"
    }


builder = StateGraph(RefundState)

builder.add_node("approval", approval_node)
builder.add_node("execute_refund", execute_refund_node)
builder.add_node("cancel_refund", cancel_refund_node)

builder.add_edge(START, "approval")
builder.add_edge("execute_refund", END)
builder.add_edge("cancel_refund", END)

checkpointer = InMemorySaver()

graph = builder.compile(
    checkpointer=checkpointer
)

config = {
    "configurable": {
        "thread_id": "refund-U1001-A1001"
    }
}


# 第一次执行：会在 approval Node 中暂停
result = graph.invoke(
    {
        "order_id": "A1001",
        "status": "waiting",
    },
    config,
)

print("第一次执行结果:")
print(result)

print("等待人工处理的信息:")
print(result["__interrupt__"])


# 第二次执行：模拟人工批准
resumed_result = graph.invoke(
    Command(
        resume={
            "approved": True
        }
    ),
    config,
)

print("恢复后的最终 State:")
print(resumed_result)