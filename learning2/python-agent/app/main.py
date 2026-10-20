import asyncio
from fastapi import FastAPI , HTTPException , Depends
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse
from app.core.config import Settings, get_settings
# from app.dependencies import get_agent_service
# from app.services.agent_service import AgentService
from app.routers.health import router as health_router
from app.routers.chat import router as chat_router
from app.schemas.chat import ChatRequest, ChatResponse
from app.routers.agent import router as agent_router
from app.routers.events import router as events_router

app = FastAPI(title="AI Customer Service Python Agent")
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(agent_router)
app.include_router(events_router)

# class ChatRequest(BaseModel):
#     message: str = Field(min_length=1, max_length=2000)

# class ChatResponse(BaseModel):
#     message: str
#     reply: str

def get_agent_context() -> dict[str, str]:
    return {
        "agent" : "customer service",
        "environment" : "dev"
    }

# async def event_generator():
#     tokens = ["你好", "，", "这是", "一条", "流式回复"]

#     for token in tokens:
#         yield f"data: {token}\n\n"
#         # yield：每次产生一段数据；
#         # data: ...\n\n：SSE 规定的事件格式；
#         await asyncio.sleep(0.5)


@app.get("/")
async def root():
    return {"service": "python-agent"}
# @app.get("/health")
# async def health():
#     return {"status": "ok"}

# @app.post("/chat",response_model=ChatResponse)
# # response_model=ChatResponse 的作用是：
# # - 定义响应结构；
# # - 自动生成响应文档；
# # - 校验返回值；
# # - 避免意外返回不应该暴露的字段。
# async def chat(request: ChatRequest) -> ChatResponse:
#     if request.message == "simulate_error":
#         raise HTTPException(status_code=503, detail="LLM service is unavailable")
#     return ChatResponse(message=request.message, reply="这是一个占位回复")

@app.get("/agent/context")
async def agent_context(
    context: dict[str, str] = Depends(get_agent_context),
    # Depends(get_agent_context) 的意思是：
    # 当前接口需要一个 context，请 FastAPI 先调用 get_agent_context()，再把返回值注入进来。
):
    return context

# @app.get("/agent/context")
# async def agent_context():
#     return get_agent_context()

@app.get("/demo/async")
async def async_demo():
    await asyncio.sleep(1)
    return {"status": "async finished"}

# @app.get("/events")
# async def events():
#     return StreamingResponse(
#         content=event_generator(),
#         media_type="text/event-stream",#text/event-stream：告诉客户端这是流式响应；
#         headers={"Cache-Control": "no-cache"},
#     )

@app.get("/config")
async def read_config(
    settings: Settings = Depends(get_settings),
):
    return {
        "app_name": settings.app_name,
        "app_env": settings.app_env,
        "debug": settings.debug,
    }

# @app.post("/agent/run", response_model=ChatResponse)
# async def run_agent(
#     request: ChatRequest,
#     service: AgentService = Depends(get_agent_service),
# ) -> ChatResponse:
#     result = await service.run(request.message)
#     return ChatResponse(**result)