from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./bot.db"

    # Zugangsdaten für twikit
    X_USERNAME: str | None = None
    X_EMAIL: str | None = None
    X_PASSWORD: str | None = None

    RUN_TOKEN: str | None = None
    USER_AGENT: str = "bvg-sbahn-bot/1.0"

settings = Settings()
