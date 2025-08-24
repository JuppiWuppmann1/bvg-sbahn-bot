from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from .settings import settings

Base = declarative_base()

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True)
    source = Column(String, nullable=False)  # BVG | SBAHN
    title = Column(Text, nullable=False)
    lines = Column(String, nullable=True)
    url = Column(String, nullable=True)
    status = Column(String, default="active")  # active | resolved
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    content_hash = Column(String, nullable=False)
    detail = Column(Text, nullable=True)

engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False  # wichtig für Zugriff nach commit()
)

def init_db():
    Base.metadata.create_all(engine)
