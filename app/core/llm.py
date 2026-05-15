from langchain_deepseek import ChatDeepSeek

from app.config import config

def get_chat_model()->ChatDeepSeek:
    return ChatDeepSeek(
        model=config.deepseek_model_name,
        api_key=config.deepseek_api_key,
        temperature=0,
    )