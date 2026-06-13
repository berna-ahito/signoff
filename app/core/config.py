from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    database_url: str = "sqlite:///./procureflow.db"
    ai_provider: str = "mock"
    groq_api_key: str = ""
    resend_api_key: str = ""
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    approval_sla_days: int = 3
    invoice_match_tolerance: float = 0.01
    run_seed_on_start: bool = False

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
