from app.agent.aiops_agent import AIOpsAgent


class AIOpsService:
    def __init__(self) -> None:
        self.agent = AIOpsAgent()

    async def diagnose(self, question: str, session_id: str, user_id: str) -> str:
        return await self.agent.run(
            question=question,
            session_id=session_id,
            user_id=user_id,
        )


aiops_service = AIOpsService()
