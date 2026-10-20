import asyncio
import os

from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
async def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL")

    if not api_key:
        raise RuntimeError("缺少 OPENAI_API_KEY")
    
    if not model:
        raise RuntimeError("缺少 OPENAI_MODEL")
    
    client_options = {"api_key": api_key}
    
    if base_url:
        client_options["base_url"] = base_url

    async with AsyncOpenAI(**client_options) as client:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业、简洁的 AI 客服助手。",
                },
                {
                    "role": "user",
                    "content": "请用一句话解释什么是 RAG。",
                },
            ],
        )

    print(response.choices[0].message.content or "")

if __name__ == "__main__":
    asyncio.run(main())