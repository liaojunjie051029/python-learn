from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.agent_service import AgentService

def get_agent_service(
        settings: Settings = Depends(get_settings),
) -> AgentService:
    return AgentService(settings)
