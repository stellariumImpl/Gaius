class AIOpsAgent:
    async def run(self, question: str, session_id: str, user_id: str = "anonymous") -> str:
        return (
            "AIOps agent is not implemented yet. "
            f"question={question}, session_id={session_id}, user_id={user_id}"
        )
