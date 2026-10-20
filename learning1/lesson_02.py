messages = [
    "用户：我的订单到哪了？",
    "Agent：准备调用订单查询工具",
]

tool_call = {
    "name": "get_order_status",
    "arguments": {
        "order_id": "A1001"
    }
}

tool_result = {
    "success": True,
    "data": {
        "status": "已发货",
        "estimated_delivery": "明天"
    },
    "error": None
}

tool_call["name"] = "cancel_order"

tool_result = {
    "success": False,
    "data": None,
    "error": "订单已经发货，无法取消"
}

print("第一条消息：", messages[0])
print("工具名称：", tool_call["name"])
print("订单号：", tool_call["arguments"]["order_id"])
print("调用是否成功：", tool_result["success"])
print("错误信息：", tool_result["error"])