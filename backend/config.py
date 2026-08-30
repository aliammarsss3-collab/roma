"""Application configuration loaded from environment variables.

Never hard-code secrets here. Copy .env.example to .env and fill in
real values before running the application.
"""
import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key")

    # --- Database ---
    # Defaults to a local SQLite file inside backend/instance/
    INSTANCE_FOLDER = os.path.join(basedir, "instance")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(INSTANCE_FOLDER, 'ruma.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Admin bootstrap account ---
    # Used only the first time the app runs, to create the initial admin user.
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-this-password")

    # --- CORS / frontend ---
    # Comma separated list of origins allowed to call the public JSON API,
    # e.g. "https://your-user.github.io"
    FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "*")

    # --- Uploads ---
    UPLOAD_FOLDER = os.path.join(basedir, "static", "uploads")
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024  # 6 MB per request

    # --- Session / cookies ---
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", default=False)

    # Set SESSION_COOKIE_SECURE=true in production (HTTPS).


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
