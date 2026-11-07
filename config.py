import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

database_url = os.environ.get("DATABASE_URL")

if database_url:
    database_url = database_url.replace(
        "postgres://", "postgresql+psycopg2://", 1
    )
    database_url = database_url.replace(
        "postgresql://", "postgresql+psycopg2://", 1
    )
    database_url = database_url.replace(
        "postgresql+psycopg://", "postgresql+psycopg2://", 1
    )


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = (
        database_url or f"sqlite:///{BASE_DIR / 'instance' / 'podologia.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True