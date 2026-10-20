import os

agent_mode = os.getenv("AGENT_MODE", "development")
max_retry_count = int(os.getenv("MAX_RETRY_COUNT", "3"))
tool_enabled_text = os.getenv("TOOL_ENABLED", "true")

tool_enabled = tool_enabled_text.strip().lower() == "true"
openai_api_key = os.getenv("OPENAI_API_KEY",'')

print("Agent 模式：", agent_mode)
print("最大重试次数：",max_retry_count)
print("工具是否启用：", tool_enabled)
print("OpenAI API Key：", '已配置' if openai_api_key != ''else '未配置')
