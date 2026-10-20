import os

agent_mode = os.getenv("AGENT_MODE", "development")

timeout_text = os.getenv("TOOL_TIMEOUT_SECONDS", "3")
tool_timeout_seconds = int(timeout_text)

max_retry_text = os.getenv("MAX_RETRY_COUNT", "3")
max_retry_count = int(max_retry_text)

openai_api_key = os.getenv("OPENAI_API_KEY")

print("Agent 模式：", agent_mode)
print("工具超时时间：", tool_timeout_seconds)
print("最大重试次数：", max_retry_count)
print("API Key 是否已配置：", bool(openai_api_key))