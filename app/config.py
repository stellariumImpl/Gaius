from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config=SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str="Gaius"
    app_version: str="0.1.0"
    debug: bool=True
    host: str="0.0.0.0"
    port: int=9900

config=Settings()