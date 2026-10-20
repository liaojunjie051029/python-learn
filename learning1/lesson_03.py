tool_identity = ("cancel_order", "v1")

allowed_tools = {
    "get_order_status",
    "cancel_order",
    "search_faq",
    "refund_order"
}

requested_tools = [
    "get_order_status",
    "cancel_order",
    "cancel_order",
    "search_faq",
    "search_faq"
]

unique_requested_tools = set(requested_tools)

print("工具名称：", tool_identity[0])
print("工具版本：", tool_identity[1])
print("cancel_order 是否允许：", "cancel_order" in allowed_tools)
print("原始工具列表：", requested_tools)
print("去重后的工具集合：", unique_requested_tools)
print("refund_order 是否允许：", "refund_order" in allowed_tools)