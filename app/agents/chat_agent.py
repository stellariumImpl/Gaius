from langchain.agents import create_agent
from langchain_core.messages import HumanMessage,SystemMessage,AIMessage

from app.tools.registry import get_chat_tools
from app.core.llm import get_chat_model

from loguru import logger

class ChatAgent:
    def __init__(self) -> None:
        self.tools = get_chat_tools()
        self.model = get_chat_model()
        self.system_prompt=self._build_system_prompt()
        self.agent = create_agent(
            self.model,
            tools=self.tools,
            system_prompt=self.system_prompt
        )
    
    def _build_system_prompt(self)->str:
        return(
            "你是一个专业、可靠的 AI 助手。\n"
            "你可以根据用户问题决定是否使用可用工具。\n"
            "回答时遵循以下原则：\n"
            "1. 优先给出准确、简洁、直接的回答。\n"
            "2. 当问题需要实时信息或工具支持时，再使用工具。\n"
            "3. 不要编造事实；不确定时明确说明。\n"
            "4. 保持自然、清晰、友好的中文表达。"
        )
        
    
    async def run(self, question: str, session_id: str) -> str:
        try:
            result = await self.agent.ainvoke(
                {"messages": [{"role": "user", "content": question}]},
                config={
                    "configurable": {
                        "thread_id": session_id,
                    }
                },
            )
            return self._extract_final_text(result)

        except Exception as e:
            logger.exception(f"chat agent run failed: session_id={session_id}, error={e}")
            return "抱歉，当前对话处理失败，请稍后重试。"

    def _extract_final_text(self, result: dict) -> str:
        messages = result.get("messages", [])
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                content = message.content
                if isinstance(content, str) and content.strip():
                    return content.strip()

        logger.warning("no final AIMessage text found in agent result")
        return "抱歉，我这次没有生成有效回复。"