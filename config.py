import os

class Config:
    # Change SECRET_KEY before deploying anywhere real
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Format: postgresql+psycopg2://<user>:<password>@<host>/<db_name>
    # IMPORTANT: don't hardcode your real password here if this goes on GitHub.
    # Set a DATABASE_URL environment variable locally instead, e.g. (Windows cmd):
    #  set DATABASE_URL=postgresql+psycopg2://postgres:shahalam06@localhost:5432/inventory_billing_db
    # The placeholder below is just so the app doesn't crash if the env var is missing.
    _raw_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:YourPassword@localhost:5432/inventory_billing_db"
    )
    if _raw_url.startswith("postgres://"):
        _raw_url = _raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
    SQLALCHEMY_DATABASE_URI = _raw_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
