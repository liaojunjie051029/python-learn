
tools = { 
    "get_order_status",
    "search_faq"
    }

def validate_tool_call(tool_call: dict) -> dict:
    try:
        if tool_call.get("name") is None:
            raise ValueError("缺少工具名称")
        tool_name = tool_call.get("name")
        if tool_name not in tools:
            return {
                "success": False,
                "data": None,
                "error": "无效的工具调用"
            }
        else:
            return {
                "success": True,
                "data": tool_call.get("arguments"),
                "error": None
            }
    except ValueError as e:
        return {
            "success": False,
            "data": None,
            "error": str(e)
        }

test1 = {"name": "get_order_status", "arguments": {"order_id": "A1001"}}
test2 = {"name": "refund_order", "arguments": {}}
test3 = {}

print(validate_tool_call(test1))
print(validate_tool_call(test2))
print(validate_tool_call(test3))

empty_tool_call = {}

print("get 读取结果：", empty_tool_call.get("name"))

try:
    print("[] 读取结果：", empty_tool_call["name"])
except KeyError as error:
    print("[] 读取失败：", error)