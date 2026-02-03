from sqlmodel import create_engine, SQLModel, Session
import os

DB_URL = os.environ.get("PVAPP_DB_URL", "sqlite:///./db.sqlite3")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})

def init_db():
    # Import models here to ensure they are registered
    from app import models  # noqa: F401
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
