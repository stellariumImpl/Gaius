from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config=SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str="Gaius"
    app_version: str="0.1.1"
    debug: bool=True
    host: str="0.0.0.0"
    port: int=9900

    deepseek_api_key: str=""
    deepseek_model_name: str="deepseek-chat"

config=Settings()