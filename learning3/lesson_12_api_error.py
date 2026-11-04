import os

import openai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
def call_model_safely(
    client: OpenAI,
    model: str,
    messages: list[dict[str, str]],
):
    try:
        return client.chat.completions.create(
            model=model,
            messages=messages,
        )

    except openai.APITimeoutError:
        print("模型请求超时，请稍后重试。")

    except openai.APIConnectionError:
        print("模型服务连接失败，请检查网络。")

    except openai.RateLimitError:
        print("请求过于频繁，请稍后重试。")

    except openai.InternalServerError:
        print("模型服务暂时异常，请稍后重试。")

    except openai.AuthenticationError:
        print("模型认证失败，请检查 API Key 和服务配置。")

    except openai.BadRequestError:
        print("模型请求参数错误，请检查 messages、model 或 tools。")

    except openai.APIStatusError as exc:
        status_code = getattr(exc, "status_code", "unknown")
        print(f"模型 API 返回错误，状态码：{status_code}")

    except openai.APIError as exc:
        # 兜底处理其他 OpenAI SDK 异常。
        # 这里只打印异常类型，不打印完整异常内容。
        print(f"未分类的模型 API 异常：{type(exc).__name__}")

    return None


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
        timeout=0.00001,
        max_retries=0,
    )

    messages = [
        {
            "role": "system",
            "content": "你是一个简洁的 AI 客服助手。",
        },
        {
            "role": "user",
            "content": "请用一句话解释什么是 RAG。",
        },
    ]

    response = call_model_safely(
        client=client,
        model=model,
        messages=messages,
    )

    if response is None:
        print("本次请求没有获得模型回答。")
        return

    print("模型回答：")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()