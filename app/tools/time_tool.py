from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

@tool
def get_current_time(timezone: str="Asia/Shanghai")->str:
    """Return the current local time for the given IANA timezone name."""
    now=datetime.now(ZoneInfo(timezone))
    return now.strftime("%Y-%m-%d %H:%M:%S")
