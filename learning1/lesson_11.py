from order_tools import get_order_status
from order_tools import cancel_order

# tool_result = get_order_status("A1001")
cancel_result = cancel_order("A1001")

# print("工具调用结果：", tool_result)
print("取消订单结果：", cancel_result)