from tools import get_order_status, cancel_order, search_faq

tool_result = get_order_status("A1001")
cancel_result = cancel_order("A1001")
search_result = search_faq("如何取消订单")


print("查询结果：", tool_result)
print("取消结果：", cancel_result)
print("faq结果：", search_result)