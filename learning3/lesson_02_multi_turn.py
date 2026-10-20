import os

from openai import OpenAI


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")

    if not api_key:
        raise RuntimeError("缺少 OPENAI_API_KEY")

    if not model:
        raise RuntimeError("缺少 LLM_MODEL")

    client_options = {"api_key": api_key}

    if base_url:
        client_options["base_url"] = base_url

    client = OpenAI(**client_options)

    messages = [
        {
            "role": "system",
            "content": "你是一个专业、准确、简洁的 AI 客服助手。",
        }
    ]

    while True:
        user_text = input("你：").strip()

        if user_text.lower() in {"exit", "quit"}:
            break

        if not user_text:
            continue

        messages.append(
            {
                "role": "user",
                "content": user_text,
            }
        )

        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )

        assistant_text = response.choices[0].message.content or ""

        messages.append(
            {
                "role": "assistant",
                "content": assistant_text,
            }
        )

        print(f"AI：{assistant_text}")


if __name__ == "__main__":
    main()