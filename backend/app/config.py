from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Oracle Access Governance"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database (PostgreSQL)
    DATABASE_URL: str = "******postgres:5432/dag_db"

    # JWT Auth
    SECRET_KEY: str = "changeme-use-a-strong-secret-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Oracle connection (privileged service account)
    # Passwords are never stored in the application DB; use env vars or a secret manager.
    ORACLE_HOST: str = "oracle"
    ORACLE_PORT: int = 1521
    ORACLE_SERVICE_NAME: str = "ORCLPDB1"
    ORACLE_ADMIN_USER: str = "C##DAG_ADMIN"
    ORACLE_ADMIN_PASSWORD: str = ""  # Set via environment variable

    # Initial admin user (created on first start)
    INITIAL_ADMIN_USERNAME: str = "admin"
    INITIAL_ADMIN_PASSWORD: str = "Admin123!"

    model_config = {"env_file": ".env", "case_sensitive": True}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
