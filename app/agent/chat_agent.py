from langchain.agents import create_agent
from langchain_core.exceptions import LangChainException
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from loguru import logger

from app.core.llm import get_chat_model
from app.tools.registry import get_chat_tools


class ChatAgent:
    def __init__(self) -> None:
        self.tools = get_chat_tools()
        self.model = get_chat_model()
        self.system_prompt = self._build_system_prompt()
        # TODO: 生产环境替换为 SqliteSaver / PostgresSaver
        self.checkpointer = InMemorySaver()
        self.agent = create_agent(
            self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            checkpointer=self.checkpointer,
        )

    def _build_system_prompt(self) -> str:
        return (
            "你是一个专业、可靠的 AI 助手。\n"
            "你可以根据用户问题决定是否使用可用工具。\n"
            "回答时遵循以下原则:\n"
            "1. 优先给出准确、简洁、直接的回答。\n"
            "2. 当问题需要实时信息或工具支持时,再使用工具。\n"
            "3. 不要编造事实;不确定时明确说明。\n"
            "4. 保持自然、清晰、友好的中文表达。"
        )

    async def run(
        self,
        question: str,
        session_id: str,
        user_id: str = "anonymous",   # TODO: 接入用户体系后改为必填
    ) -> str:
        thread_id = f"{user_id}:{session_id}"
        try:
            result = await self.agent.ainvoke(
                {"messages": [{"role": "user", "content": question}]},
                config={"configurable": {"thread_id": thread_id}},
            )
            return self._extract_final_text(result)

        except LangChainException:
            # LLM 层可预期错误: 限流、超时、上下文超长、工具调用失败等
            logger.warning(f"langchain error: thread_id={thread_id}")
            return "抱歉,模型暂时无法响应,请稍后重试。"

        except Exception:
            # 真正的代码 bug / 配置错误,记完日志重新抛出,让上层(FastAPI)返 500
            logger.exception(f"unexpected error: thread_id={thread_id}")
            raise

    @staticmethod
    def _extract_final_text(result: dict) -> str:
        messages = result.get("messages", [])
        for message in reversed(messages):
            if not isinstance(message, AIMessage):
                continue

            content = message.content

            # 情况 1: content 是纯字符串(最常见)
            if isinstance(content, str):
                text = content.strip()
                if text:
                    return text

            # 情况 2: content 是 block 列表(thinking 模式 / 多模态)
            # 例如: [{"type": "thinking", "thinking": "..."}, {"type": "text", "text": "..."}]
            elif isinstance(content, list):
                text_parts = [
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                text = "".join(text_parts).strip()
                if text:
                    return text

        logger.warning("no final AIMessage text found in agent result")
        return "抱歉,我这次没有生成有效回复。"