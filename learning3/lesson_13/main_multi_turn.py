import os

import openai
from fastapi import FastAPI, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL")

if not api_key or not base_url or not model:
    raise RuntimeError(
        "请先设置 OPENAI_API_KEY、OPENAI_BASE_URL 和 OPENAI_MODEL"
    )


client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=20.0,
    max_retries=0,
)

app = FastAPI(title="Python AI Customer Service")

SYSTEM_PROMPT = "你是一个简洁、专业的 AI 客服助手。"

MAX_HISTORY_MESSAGES = 6

# 仅用于学习，重启服务后数据会消失
conversation_store: dict[str, list[dict[str, str]]] = {}


class ChatRequest(BaseModel):
    session_id: str = Field(
        min_length=1,
        max_length=100,
    )
    message: str = Field(
        min_length=1,
        max_length=2000,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
    }


@app.post("/chat")
async def chat(request: ChatRequest) -> dict:
    history = conversation_store.get(
        request.session_id,
        [],
    )

    recent_history = history[-MAX_HISTORY_MESSAGES:]

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        *recent_history,
        {
            "role": "user",
            "content": request.message,
        },
    ]

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
        )

    except openai.APITimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="模型请求超时，请稍后重试。",
        ) from exc

    except openai.APIConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail="模型服务连接失败，请稍后重试。",
        ) from exc

    except openai.RateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁，请稍后重试。",
        ) from exc

    except openai.AuthenticationError as exc:
        raise HTTPException(
            status_code=500,
            detail="模型服务配置错误。",
        ) from exc

    except openai.BadRequestError as exc:
        raise HTTPException(
            status_code=400,
            detail="模型请求参数错误。",
        ) from exc

    except openai.InternalServerError as exc:
        raise HTTPException(
            status_code=502,
            detail="模型服务暂时异常。",
        ) from exc

    except openai.APIError as exc:
        raise HTTPException(
            status_code=502,
            detail="模型服务调用失败。",
        ) from exc

    answer = response.choices[0].message.content or ""

    # 只有模型成功返回后，才保存本轮对话
    session_history = conversation_store.setdefault(
        request.session_id,
        [],
    )

    session_history.extend(
        [
            {
                "role": "user",
                "content": request.message,
            },
            {
                "role": "assistant",
                "content": answer,
            },
        ]
    )

    # 只保留最近几条消息
    del session_history[:-MAX_HISTORY_MESSAGES]

    usage = None

    if response.usage is not None:
        usage = response.usage.model_dump()

    return {
        "session_id": request.session_id,
        "answer": answer,
        "usage": usage,
    }