from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from .settings import settings

Base = declarative_base()

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True)
    source = Column(String, nullable=False)   # BVG oder SBAHN
    title = Column(Text, nullable=False)
    lines = Column(String, nullable=True)
    url = Column(String, nullable=True)
    status = Column(String, default="active") # active | resolved
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    content_hash = Column(String, nullable=False)
    detail = Column(Text, nullable=True)

engine = create_engine(settings.DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    Base.metadata.create_all(engine)

# Speichern oder Aktualisieren
def save_entry(entry):
    with SessionLocal() as session:
        existing = session.get(Incident, entry.id)
        if existing:
            existing.last_seen = datetime.utcnow()
            existing.status = "active"
            existing.title = entry.title
            existing.lines = entry.lines
            existing.url = entry.url
            existing.detail = entry.detail
            existing.content_hash = entry.content_hash
        else:
            session.add(entry)
        session.commit()

# Alle aktiven Incidents abrufen
def get_active_incidents():
    with SessionLocal() as session:
        return session.query(Incident).filter(Incident.status == "active").all()

# Incident als gelöst markieren
def mark_resolved(incident_id):
    with SessionLocal() as session:
        inc = session.get(Incident, incident_id)
        if inc:
            inc.status = "resolved"
            inc.last_seen = datetime.utcnow()
            session.commit()
