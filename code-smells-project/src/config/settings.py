"""Application configuration — sourced from the environment, never hardcoded.

Fixes AP-SEC-01 (hardcoded secrets) and AP-SEC-06 (debug in prod).
See .env.example for the variables this reads.
"""
import os


class Config:
    # Secret comes from the environment. The fallback is clearly dev-only and
    # must be overridden in any real deployment.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

    # Debug defaults to OFF (production-safe). Enable explicitly for local dev.
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")

    # Admin endpoints are disabled unless a token is configured. Callers must
    # send it in the X-Admin-Token header (fixes AP-SEC-05).
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

    # Persistence
    DB_PATH = os.environ.get("DB_PATH", "loja.db")

    # Server
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))
