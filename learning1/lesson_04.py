tool_result = {
    "success": True,
    "data": {
        "status": "已发货"
    },
    "error": None
}

if tool_result["success"]:
    print("Agent：工具调用成功")
else:
    print("Agent：工具调用失败")
    print("失败原因：", tool_result["error"])

