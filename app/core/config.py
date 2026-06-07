from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = "sqlite:///./procureflow.db"
    ai_provider: str = "mock"
    groq_api_key: str = ""
    slack_webhook_url: str = ""
    app_env: str = "development"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
