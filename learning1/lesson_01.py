user_message = "我的订单到哪了？"
tool_name = "get_order_status"
max_retry_count = 2
tool_enabled = True
agent_state = "waiting_for_tool"

print("用户消息：", user_message)
print("准备调用工具：", tool_name)
print("最大重试次数：", max_retry_count)
print("工具是否启用：", tool_enabled)
print("Agent 当前状态：", agent_state)