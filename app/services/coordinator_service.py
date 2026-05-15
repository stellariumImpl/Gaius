class CoordinatorService:
    async def route(
        self,
        question: str,
        session_id: str,
        user_id: str,
    ) -> str:
        return (
            "Coordinator is not implemented yet. "
            f"question={question}, session_id={session_id}, user_id={user_id}"
        )


coordinator_service = CoordinatorService()
