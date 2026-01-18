from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8080
    database_url: str = "sqlite+aiosqlite:///./data/factory.db"
    db_echo: bool = False
    env: str = "development"

    class Config:
        env_file = ".env"
        env_prefix = "FACTORY_"


settings = Settings()
