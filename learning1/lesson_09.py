def get_order_status(order_id: str) -> dict:
    try:
        if not order_id:
            raise ValueError("order_id 不能为空")

        if order_id == "A1001":
            return {
                "success": True,
                "data": {
                    "order_id": order_id,
                    "status": "已发货"
                },
                "error": None
            }

        # 订单不存在属于正常业务失败，不需要抛异常
        return {
            "success": False,
            "data": None,
            "error": "订单不存在"
        }

    except ValueError as error:
        return {
            "success": False,
            "data": None,
            "error": str(error)
        }


tool_result = get_order_status("A1001")

print("调用结果：", tool_result)