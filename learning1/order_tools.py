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

def cancel_order(order_id: str) -> dict:
    return {
        "success": False,
        "data": None,
        "error": "订单已经发货，无法取消"
    }