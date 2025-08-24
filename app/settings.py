from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Sicherheit
    RUN_TOKEN: str
    USER_AGENT: str = "Mozilla/5.0 (...)"

    # Twikit Account-Daten
    TWIKIT_USERNAME: str
    TWIKIT_PASSWORD: str
    TWIKIT_EMAIL: str

    # Optional
    SESSION_FILE: str = "twikit_session.json"
    DATABASE_URL: str = "sqlite:///./app.db"

    # Tweet-Service
    TWEET_SERVICE_URL: str  # <––– Das fehlt aktuell!

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Globale Instanz
settings = Settings()
