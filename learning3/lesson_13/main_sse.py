import json
import os
from collections.abc import AsyncIterator
from pydantic import BaseModel, Field
import openai
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is not set")
    return value


app = FastAPI()

client = AsyncOpenAI(
    api_key=required_env("OPENAI_API_KEY"),
    base_url=required_env("OPENAI_BASE_URL"),
    timeout=20.0,
    max_retries=0,
)

MODEL = required_env("OPENAI_MODEL")

class StreamRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
def make_sse_data(payload: object) -> str:
    """
    把 Python 对象包装成一条 SSE 消息。
    SSE 消息必须以两个换行符结束。
    """
    data = json.dumps(payload, ensure_ascii=False)
    return f"data: {data}\n\n"


async def generate_sse(message: str) -> AsyncIterator[str]:
    try:
        stream = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的 AI 客服，请简洁、准确地回答问题。",
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            stream=True,
        )

        async for chunk in stream:
            if not chunk.choices:
                continue

            content = chunk.choices[0].delta.content

            if content:
                yield make_sse_data({
                    "content": content,
                })

        yield "data: [DONE]\n\n"

    except openai.APITimeoutError:
        yield "event: error\n"
        yield make_sse_data({
            "code": "timeout",
            "message": "模型请求超时，请稍后重试。",
        })

    except openai.APIError:
        yield "event: error\n"
        yield make_sse_data({
            "code": "model_api_error",
            "message": "模型服务暂时不可用，请稍后重试。",
        })


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/chat/stream")
async def chat_stream(
    message: str = Query(..., min_length=1, max_length=2000),
):
    return StreamingResponse(
        generate_sse(message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

@app.post("/chat/stream-post")
async def chat_stream_post(request: StreamRequest):
    return StreamingResponse(
        generate_sse(request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )