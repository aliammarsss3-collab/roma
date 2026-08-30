"""Application factory for منتجع رُومة (Ruma Resort) backend."""
import os

from flask import Flask, render_template, jsonify, request

from config import config_by_name
from extensions import db, login_manager, csrf, cors

DEFAULT_SETTINGS = {
    "resort_name_ar": "منتجع رُومة",
    "resort_tagline": "مكانكم المثالي للراحة، والرفاهية وقضاء أجمل الأوقات",
    "about_text": (
        "يقدّم منتجع رُومة تجربة استجمام فاخرة بين أحضان الطبيعة، حيث تلتقي "
        "الرفاهية بالهدوء. مساحات خضراء واسعة، خدمة راقية، وتفاصيل مصمّمة "
        "بعناية لتمنحكم وقتاً لا يُنسى بعيداً عن صخب المدينة."
    ),
    "morning_price": "200000",
    "evening_price": "250000",
    "morning_hours": "من 10 صباحاً إلى 6 مساءً",
    "evening_hours": "من 8 مساءً إلى 8 صباحاً",
    "phone": "07762052560",
    "whatsapp": "9647762052560",
    "address": "منتجع رُومة - العراق",
    "services": (
        "حمام سباحة خاص|مساحات خضراء واسعة|جلسات خارجية مفروشة|"
        "أمن وخصوصية تامة|مواقف سيارات مجانية|خدمة تنظيف متكاملة"
    ),
}


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    # --- Extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    origins = app.config["FRONTEND_ORIGIN"]
    origins = [o.strip() for o in origins.split(",")] if origins != "*" else "*"
    cors.init_app(app, resources={r"/api/*": {"origins": origins}})

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["INSTANCE_FOLDER"], exist_ok=True)

    # --- Blueprints ---
    from api import api_bp
    from admin import admin_bp

    csrf.exempt(api_bp)  # public JSON API, no session cookies involved

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Error handlers ---
    @app.errorhandler(404)
    def not_found(_e):
        if request.path.startswith("/api/"):
            return jsonify(success=False, error="not_found"), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        if request.path.startswith("/api/"):
            return jsonify(success=False, error="server_error"), 500
        return render_template("errors/500.html"), 500

    @app.route("/")
    def index():
        return jsonify(
            service="ruma-resort-backend",
            status="running",
            docs="راجع README الخاص بالمشروع لمعرفة نقاط الوصول المتاحة (API_BASE_URL/api/...)",
            admin="/admin/login",
        )

    with app.app_context():
        _bootstrap(app)

    return app


def _bootstrap(app):
    """Create tables, the initial admin user, and default settings if missing."""
    from models import User, Setting

    db.create_all()

    admin_username = app.config["ADMIN_USERNAME"]
    if not User.query.filter_by(username=admin_username).first():
        admin = User(username=admin_username)
        admin.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(admin)

    for key, value in DEFAULT_SETTINGS.items():
        if not Setting.query.filter_by(key=key).first():
            db.session.add(Setting(key=key, value=value))

    db.session.commit()


app = create_app()


@app.cli.command("create-admin")
def create_admin_cli():
    """Create (or reset the password of) the admin user from env vars.

    Usage: flask --app app create-admin
    """
    from models import User

    username = app.config["ADMIN_USERNAME"]
    password = app.config["ADMIN_PASSWORD"]
    user = User.query.filter_by(username=username).first()
    if user is None:
        user = User(username=username)
        db.session.add(user)
        print(f"تم إنشاء المستخدم الإداري: {username}")
    else:
        print(f"تم تحديث كلمة مرور المستخدم الإداري: {username}")
    user.set_password(password)
    db.session.commit()


if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False), port=int(os.environ.get("PORT", 5000)))
