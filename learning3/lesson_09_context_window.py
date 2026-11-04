import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def build_messages(
    system_prompt: str,
    history: list[dict[str, str]],
    current_user_message: str,
    max_turns: int,
) -> list[dict[str, str]]:
    """
    history 中只放 user 和 assistant 消息。

    max_turns=2 表示最多保留最近两轮 user/assistant 对话。
    """
    if max_turns < 0:
        raise ValueError("max_turns 不能小于 0")

    recent_history = history[-max_turns * 2:] if max_turns > 0 else []

    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        *recent_history,
        {
            "role": "user",
            "content": current_user_message,
        },
    ]


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL")

    if not api_key or not base_url or not model:
        raise RuntimeError(
            "请先设置 OPENAI_API_KEY、OPENAI_BASE_URL 和 OPENAI_MODEL"
        )

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=20.0,
        max_retries=0,
    )

    history = [
        {
            "role": "user",
            "content": "我叫小王。",
        },
        {
            "role": "assistant",
            "content": "好的，我会记住你叫小王。",
        },
        {
            "role": "user",
            "content": "我正在排查一台挖掘机。",
        },
        {
            "role": "assistant",
            "content": "明白，目前设备是挖掘机。",
        },
        {
            "role": "user",
            "content": "启动电机完全没有反应。",
        },
        {
            "role": "assistant",
            "content": "这种情况应优先检查电瓶、搭铁线和启动控制回路。",
        },
    ]

#统提示词通常包含：
# - 角色；
# - 业务边界；
# - 安全规则；
# - 输出格式；
# - 客服行为规范；
# - 哪些问题不能回答。
    messages = build_messages(
        system_prompt="你是专业的设备售后客服，请回答简洁。",
        history=history,
        current_user_message="我现在应该先检查什么？",
        max_turns=1,
    )

    print("本次发送的消息：")
    for message in messages:
        print(f"{message['role']}: {message['content']}")

    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )

    print("\n模型回答：")
    print(response.choices[0].message.content)

    if response.usage:
        print("\nToken 使用情况：")
        print("输入 Token：", response.usage.prompt_tokens)
        print("输出 Token：", response.usage.completion_tokens)
        print("总 Token：", response.usage.total_tokens)


if __name__ == "__main__":
    main()