from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ServerPulse API"
    database_url: str = (
        "postgresql+psycopg://serverpulse:serverpulse_dev"
        "@localhost:5432/serverpulse"
    )
    prometheus_url: str = "http://localhost:9090"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
