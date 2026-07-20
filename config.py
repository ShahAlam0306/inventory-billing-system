import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    _raw_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:YourPassword@localhost:5432/inventory_billing_db"
    )

    if _raw_url.startswith("postgres://"):
        _raw_url = _raw_url.replace("postgres://", "postgresql+psycopg://", 1)

    if _raw_url.startswith("postgresql://"):
        _raw_url = _raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

    SQLALCHEMY_DATABASE_URI = _raw_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
