from app.tools.time_tool import get_current_time

def get_chat_tools()->list:
    return [get_current_time]

def get_aiops_tools()->list:
    return []