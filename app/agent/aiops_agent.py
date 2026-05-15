from langchain.agents import create_agent
from langchain_core.exceptions import LangChainException
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from loguru import logger

from app.core.context_builder import build_chat_input
from app.core.llm import get_chat_model
from app.tools.registry import get_aiops_tools


class AIOpsAgent:
    def __init__(self) -> None:
        self.tools = get_aiops_tools()
        self.model = get_chat_model()
        self.system_prompt = self._build_system_prompt()
        self.checkpointer = InMemorySaver()
        self.agent = create_agent(
            self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            checkpointer=self.checkpointer,
        )

    def _build_system_prompt(self) -> str:
        return (
            "你是一个专业的 AIOps 运维助手。\n"
            "你的职责是帮助用户分析系统问题、定位风险、提供排查思路和处理建议。\n"
            "回答时遵循以下原则:\n"
            "1. 优先给出结构清晰的诊断思路。\n"
            "2. 如果信息不足,明确指出缺少哪些关键信息。\n"
            "3. 不编造日志、指标或故障事实。\n"
            "4. 回答时尽量包含: 现象判断、可能原因、排查步骤、建议动作。\n"
            "5. 保持专业、简洁、直接的中文表达。"
        )

    async def run(
        self,
        question: str,
        session_id: str,
        user_id: str = "anonymous",
    ) -> str:
        thread_id = f"{user_id}:{session_id}"
        agent_input = build_chat_input(question=question)

        try:
            result = await self.agent.ainvoke(
                agent_input,
                config={"configurable": {"thread_id": thread_id}},
            )
            return self._extract_final_text(result)

        except LangChainException:
            logger.warning(f"aiops langchain error: thread_id={thread_id}")
            return "抱歉,当前诊断请求暂时无法处理,请稍后重试。"

        except Exception:
            logger.exception(f"aiops unexpected error: thread_id={thread_id}")
            raise

    @staticmethod
    def _extract_final_text(result: dict) -> str:
        messages = result.get("messages", [])
        for message in reversed(messages):
            if not isinstance(message, AIMessage):
                continue

            content = message.content

            if isinstance(content, str):
                text = content.strip()
                if text:
                    return text

            elif isinstance(content, list):
                text_parts = [
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                text = "".join(text_parts).strip()
                if text:
                    return text

        logger.warning("no final AIMessage text found in aiops result")
        return "抱歉,我这次没有生成有效诊断结果。"
