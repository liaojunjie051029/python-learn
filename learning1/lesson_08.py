tool_name: str = "get_order_status"
max_retry_count: int = 3
tool_enabled: bool = True


def get_order_status(order_id: str) -> dict:
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


tool_result: dict = get_order_status("A1001")

print("工具名称：", tool_name)
print("最大重试次数：", max_retry_count)
print("工具是否启用：", tool_enabled)
print("调用结果：", tool_result)