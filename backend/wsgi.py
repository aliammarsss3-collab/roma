"""Entry point for production WSGI servers (e.g. gunicorn).

Example:
    gunicorn wsgi:app --bind 0.0.0.0:8000
"""
from app import app

if __name__ == "__main__":
    app.run()
