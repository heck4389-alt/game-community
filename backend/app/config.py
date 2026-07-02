from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    site_name: str = "게임프리 커뮤니티"
    site_tagline: str = "게임 정보와 팁을 함께 나누는 공간"
    admin_usernames: str = "jeon6974"

    database_url: str = "postgresql+psycopg://boarduser:boardpass@localhost:5432/boarddb"
    secret_key: str = "dev-secret-key-change-in-production"
    app_env: str = "development"
    debug: bool = True
    session_cookie_name: str = "board_session"
    session_max_age: int = 60 * 60 * 24 * 7  # 7 days

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        return value


settings = Settings()
