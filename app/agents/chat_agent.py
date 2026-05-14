from app.tools.registry import get_chat_tools

class ChatAgent:
    def __init__(self) -> None:
        self.tools = get_chat_tools()
    
    async def run(self,question:str,session_id:str)->str:
        tool_names=[tool.name for tool in self.tools if hasattr(tool,"name")]
        return(
            f"chat agent received question: {question} | "
            f"session_id: {session_id} | "
            f"available_tools: {tool_names}"
        )