from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Sicherheit
    RUN_TOKEN: str
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

    # Twikit Account-Daten
    TWIKIT_USERNAME: str
    TWIKIT_PASSWORD: str
    TWIKIT_EMAIL: str

    # DB
    DATABASE_URL: str = "sqlite:///./app.db"

    # Tweet-Service (optional default, damit kein Crash beim Start)
    TWEET_SERVICE_URL: str = ""
    TWEET_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
