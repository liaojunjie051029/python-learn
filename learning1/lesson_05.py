requested_tools = [
    "get_order_status",
    "cancel_order",
    "refund_order",
    "search_faq"
]

allowed_tools = {
    "get_order_status",
    "cancel_order",
    "refund_order"
}

for tool_name in requested_tools:
    if tool_name in allowed_tools:
        print("允许调用：", tool_name)
    else:
        print("拒绝调用：", tool_name)