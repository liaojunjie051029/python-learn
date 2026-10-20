from fastapi import APIRouter, HTTPException #导入路由和http错误处理

from app.schemas.chat import ChatRequest, ChatResponse #导入请求和响应数据结构

router = APIRouter(tags=["chat"])

@router.post("/chat",response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if request.message == "simulate_error":
        raise HTTPException(
            status_code=503,
            detail="LLM service is unavailable",
        )
    return ChatResponse(message=request.message, reply="这是一个占位回复")
    