from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Sicherheit
    RUN_TOKEN: str
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

    # Twikit Account-Daten
    TWIKIT_USERNAME: str
    TWIKIT_PASSWORD: str
    TWIKIT_EMAIL: str

    # Optional: Pfad zur gespeicherten Session (damit Login nicht jedes Mal neu nötig ist)
    SESSION_FILE: str = "twikit_session.json"

    # Datenbank: Fallback auf SQLite, falls nichts gesetzt ist
    DATABASE_URL: str = "sqlite:///./app.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Globale Instanz
settings = Settings()
