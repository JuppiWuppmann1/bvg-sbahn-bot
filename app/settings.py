from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Sicherheit
    RUN_TOKEN: str

    # Twikit Account-Daten
    TWIKIT_USERNAME: str
    TWIKIT_PASSWORD: str
    TWIKIT_EMAIL: str

    # Optional: Pfad zur gespeicherten Session (damit Login nicht jedes Mal neu nötig ist)
    SESSION_FILE: str = "twikit_session.json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Globale Instanz
settings = Settings()
