"""
Pytest configuration and fixtures.
Sets environment variables before any application code is imported
so that database.py can create a valid (SQLite) engine for unit tests.
"""
import os
import pytest

# Set test environment BEFORE any app imports so that database.py
# uses a lightweight in-memory SQLite engine instead of requiring PostgreSQL.
os.environ.setdefault(
    "DATABASE_URL",
    "sqlite:///./test_dag.db",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-production")
os.environ.setdefault("ORACLE_ADMIN_PASSWORD", "")
