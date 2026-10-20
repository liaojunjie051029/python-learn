def get_order_status(order_id):
    if order_id == "A1001":
        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "status": "已发货"
            },
            "error": None
        }

    return {
        "success": False,
        "data": None,
        "error": "订单不存在"
    }


tool_result = get_order_status("A1001")

print("调用是否成功：", tool_result["success"])
print("工具结果：", tool_result)