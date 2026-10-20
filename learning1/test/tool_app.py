from tool_models import Tool

get_order_status = Tool(
    name="get_order_status",
    description="获取订单状态",
    enabled=True
)
cancel_order = Tool(
    name="cancel_order",
    description="取消订单",
    enabled=False
)

print(get_order_status.summary())
print(cancel_order.summary())