from typing import Callable

class tool:
    def __init__(self,name:str,description:str,handler:Callable[..., dict],enabled:bool=True):
        self.name = name
        self.description = description
        self.handler = handler
        self.enabled = enabled


def get_order_status_handler(order_id:str) -> dict:
    return {
        "success": True,
        "data": {
            "order_id": order_id,
            "status": "已发货"
        },
        "error": None
    }
def search_faq_handler() -> dict:
    return {
        "success": True,
        "data": [
            {
                "question": "如何查询订单状态",
                "answer": "请使用get_order_status工具查询"
            },
            {
                "question": "如何取消订单",
                "answer": "请使用cancel_order工具取消"
            }
        ],
        "error": None
    }
def cancel_order_handler(order_id:str) -> dict:
    return {
    "success": False,
    "data": None,
    "error": "订单已经发货，无法取消"
}
    
get_order_status = tool(
    name="get_order_status",
    description="获取订单状态",
    handler=get_order_status_handler,
    enabled=True
)

search_faq = tool(
    name="search_faq",
    description="搜索常见问题",
    handler=search_faq_handler,
    enabled=True
)

cancel_order = tool(
    name="cancel_order",
    description="取消订单",
    handler=cancel_order_handler,
    enabled=False
)

tool_registry = {
    "get_order_status": get_order_status,
    "search_faq": search_faq,
    "cancel_order": cancel_order,
}


def execute_tool(tool_name: str, arguments: dict) -> dict:
    try:
        tool = tool_registry.get(tool_name)
        if tool is None:
            raise ValueError("无效的工具调用")

        if not tool.enabled:
            raise ValueError("工具已禁用")

        return tool.handler(**arguments)

        
    except (ValueError, TypeError) as e:
        return {
            "success": False,
            "data": None,
            "error": str(e)
        }

print(execute_tool(
    "get_order_status",
    {"order_id": "A1001"}
))

print(execute_tool(
    "search_faq",
    {}
))

print(execute_tool(
    "refund_order",
    {}
))

print(execute_tool(
    "cancel_order",
    {"order_id": "A1001"}
))

print(execute_tool(
    "get_order_status",
    {}
))