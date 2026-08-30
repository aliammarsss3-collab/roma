"""SQLAlchemy models: User, Booking, Setting, GalleryImage."""
import secrets
import string
from datetime import datetime, date

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


def _utcnow():
    return datetime.utcnow()


class User(UserMixin, db.Model):
    """Admin user account."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.username}>"


# Human-readable Arabic labels for booking statuses.
BOOKING_STATUSES = {
    "new": "جديد",
    "pending": "قيد المراجعة",
    "confirmed": "مؤكد",
    "rejected": "مرفوض",
    "completed": "مكتمل",
}

SHIFT_LABELS = {
    "morning": "الشفت الصباحي (10 صباحاً - 6 مساءً)",
    "evening": "الشفت المسائي (8 مساءً - 8 صباحاً)",
}


def generate_booking_id():
    """Generate a short, unique, human-shareable booking reference."""
    alphabet = string.ascii_uppercase + string.digits
    while True:
        suffix = "".join(secrets.choice(alphabet) for _ in range(6))
        candidate = f"RUMA-{suffix}"
        if not Booking.query.filter_by(booking_id=candidate).first():
            return candidate


class Booking(db.Model):
    """A booking request submitted by a guest through the public site."""

    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(20), unique=True, nullable=False, index=True)

    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False, index=True)
    booking_date = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(10), nullable=False)  # "morning" | "evening"
    guests_count = db.Column(db.Integer, nullable=False, default=1)
    notes = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(20), nullable=False, default="new", index=True)

    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    @property
    def status_label(self):
        return BOOKING_STATUSES.get(self.status, self.status)

    @property
    def shift_label(self):
        return SHIFT_LABELS.get(self.shift, self.shift)

    def to_public_dict(self):
        """Minimal, safe representation for the public status-check endpoint."""
        return {
            "booking_id": self.booking_id,
            "status": self.status,
            "status_label": self.status_label,
            "booking_date": self.booking_date.isoformat(),
            "shift": self.shift,
            "shift_label": self.shift_label,
        }

    def __repr__(self):
        return f"<Booking {self.booking_id} {self.status}>"


class Setting(db.Model):
    """Simple key/value store for editable site content (prices, resort info)."""

    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False, default="")

    @staticmethod
    def get(key, default=""):
        row = Setting.query.filter_by(key=key).first()
        return row.value if row else default

    @staticmethod
    def set(key, value):
        row = Setting.query.filter_by(key=key).first()
        if row is None:
            row = Setting(key=key, value=value)
            db.session.add(row)
        else:
            row.value = value
        db.session.commit()
        return row

    @staticmethod
    def get_many(keys):
        rows = Setting.query.filter(Setting.key.in_(keys)).all()
        return {row.key: row.value for row in rows}


class GalleryImage(db.Model):
    """An image shown in the public photo gallery."""

    __tablename__ = "gallery_images"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(255), nullable=True, default="")
    uploaded_at = db.Column(db.DateTime, default=_utcnow)

    def to_dict(self, base_url=""):
        return {
            "id": self.id,
            "caption": self.caption or "",
            "url": f"{base_url}/static/uploads/{self.filename}",
        }
