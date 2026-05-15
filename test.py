# test.py
import asyncio
from app.agent.chat_agent import ChatAgent


async def main():
    agent = ChatAgent()

    # 测试 1: 基础对话
    r1 = await agent.run("你好,介绍一下你自己", session_id="s1", user_id="u1")
    print(f"[Test 1] {r1}\n")

    # 测试 2: 多轮记忆(checkpointer 生效的关键测试)
    await agent.run("我叫小明,记住了", session_id="s2", user_id="u1")
    r2 = await agent.run("我叫什么?", session_id="s2", user_id="u1")
    print(f"[Test 2] {r2}")
    if "小明" in r2:
        print("✅ checkpointer 工作正常,多轮记忆 OK\n")
    else:
        print("❌ checkpointer 没生效,模型没记住\n")

    # 测试 3: 用户隔离(同 session_id, 不同 user_id, 不应串号)
    await agent.run("我叫张三", session_id="s3", user_id="u2")
    r3 = await agent.run("我叫什么?", session_id="s3", user_id="u3")
    print(f"[Test 3] {r3}")
    if "张三" not in r3:
        print("✅ 用户隔离 OK,跨用户没串号\n")
    else:
        print("❌ 用户串号了,thread_id 拼接没生效\n")


if __name__ == "__main__":
    asyncio.run(main())
