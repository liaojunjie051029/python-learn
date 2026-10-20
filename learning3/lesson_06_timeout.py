import os

import openai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL")

    if not api_key:
        raise RuntimeError("缺少 OPENAI_API_KEY")
    
    if not model:
        raise RuntimeError("缺少 OPENAI_MODEL")
    
    client_options: dict[str, object] = {
        "api_key": api_key,

        # 本次请求最多等待约 20 秒
        "timeout": 20.0,

        # 先关闭自动重试，方便观察超时行为
        # 重试会在下一小节学习
        "max_retries": 0,
    }
    
    if base_url:
        client_options["base_url"] = base_url

    client = OpenAI(**client_options)

    try:
        response = client.chat.completions.create(
            model = model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个简洁的 AI 客服助手。",
                },
                {
                    "role": "user",
                    "content": "请用三句话解释什么是 RAG。",
                },
            ],
        )

        answer = response.choices[0].message.content or ""
        print(answer)

    except openai.APITimeoutError:
        print("请求超时:模型在规定时间内没有完成响应。")

    except openai.APIConnectionError as e:
        print(f"网络连接失败: {e}")

if __name__ == "__main__":
    main()