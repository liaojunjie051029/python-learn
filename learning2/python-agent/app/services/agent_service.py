from app.core.config import Settings
from dataclasses import dataclass

@dataclass
class AgentService:
    settings: Settings

    async def run(self, message: str) -> dict[str, str]:
        return {"message": message, "reply": f"[{self.settings.app_env} Agent 已收到：{message}]"}