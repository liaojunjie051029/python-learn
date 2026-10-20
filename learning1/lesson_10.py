import json

agent_state = {
    "conversation_id": "conv-001",
    "last_tool": "get_order_status",
    "retry_count": 3,
    "tool_result": {
        "success": True,
        "data": {
            "order_id": "A1001",
            "status": "已签收"
        },
        "error": None
    }
}

with open("agent_state.json", "w", encoding="utf-8") as file:
    json.dump(
        agent_state,
        file,
        ensure_ascii=False,#不要把中文转换成 Unicode 转义字符
        indent=2#表示 JSON 嵌套时每一层缩进 2 个空格。
    )

with open("agent_state.json", "r", encoding="utf-8") as file:
    loaded_state = json.load(file)#加载 JSON 文件

print("最后调用工具：", loaded_state["last_tool"])
print("重试次数：", loaded_state["retry_count"])
print("订单状态：", loaded_state["tool_result"]["data"]["status"])