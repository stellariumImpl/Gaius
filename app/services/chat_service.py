from app.agent.chat_agent import ChatAgent

class ChatService:
    def __init__(self) -> None:
        self.agent = ChatAgent()

    async def chat(self, question: str, session_id: str, user_id: str) -> str:
        return await self.agent.run(
            question=question,
            session_id=session_id,
            user_id=user_id,
        )


chat_service = ChatService()