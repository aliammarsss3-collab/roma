"""Central place for Flask extension instances, to avoid circular imports."""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_cors import CORS

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
cors = CORS()

login_manager.login_view = "admin.login"
login_manager.login_message = "الرجاء تسجيل الدخول للوصول إلى لوحة التحكم."
login_manager.login_message_category = "warning"
