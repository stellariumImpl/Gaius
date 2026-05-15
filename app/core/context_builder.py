def build_chat_input(question: str) -> dict:
    return {
        "messages": [
            {
                "role": "user",
                "content": question,
            }
        ]
    }
