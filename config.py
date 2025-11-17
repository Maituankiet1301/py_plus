import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        os.environ.get("SQLALCHEMY_DATABASE_URI", f"sqlite:///{os.path.join(basedir, 'inventory.db')}")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    ITEMS_PER_PAGE = int(os.environ.get("ITEMS_PER_PAGE", 20))
    JWT_EXPIRATION_DELTA = timedelta(hours=8)
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
    MIGRATIONS_DIR = os.environ.get("MIGRATIONS_DIR", "migrations")
