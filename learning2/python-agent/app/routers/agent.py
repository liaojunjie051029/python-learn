from fastapi import APIRouter, Depends

from app.dependencies import get_agent_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.agent_service import AgentService


router = APIRouter(
    prefix="/agent",#prefix="/agent"是添加路径前缀
    tags=["agent"],
)


@router.post("/run", response_model=ChatResponse)
async def run_agent(
    request: ChatRequest,
    service: AgentService = Depends(get_agent_service),
) -> ChatResponse:
    result = await service.run(request.message)
    return ChatResponse(**result)