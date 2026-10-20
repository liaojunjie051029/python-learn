import asyncio

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["events"])

async def event_generator():
    tokens = ["你好", "，", "这是", "一条", "流式回复"]

    for token in tokens:
        yield f"data: {token}\n\n"
        await asyncio.sleep(0.5)


@router.get("/events")
async def events():
    return StreamingResponse(
        content=event_generator(),
        media_type="text/event-stream",#text/event-stream：告诉客户端这是流式响应；
        headers={"Cache-Control": "no-cache"},
    )