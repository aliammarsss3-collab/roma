"""Public JSON API consumed by the static frontend.

No authentication is required here on purpose: these are the endpoints
the GitHub Pages frontend calls directly from the browser. Keep this
blueprint limited to safe, read-only data plus booking creation.
"""
from datetime import datetime, date

from flask import Blueprint, jsonify, request

from extensions import db
from models import Booking, Setting, GalleryImage, generate_booking_id

api_bp = Blueprint("api", __name__)

PUBLIC_SETTING_KEYS = [
    "resort_name_ar",
    "resort_tagline",
    "about_text",
    "morning_price",
    "evening_price",
    "morning_hours",
    "evening_hours",
    "phone",
    "whatsapp",
    "address",
    "services",
]


@api_bp.get("/health")
def health():
    return jsonify(success=True, status="ok")


@api_bp.get("/settings")
def get_settings():
    values = Setting.get_many(PUBLIC_SETTING_KEYS)
    services_raw = values.get("services", "")
    values["services"] = [s for s in services_raw.split("|") if s.strip()]
    return jsonify(success=True, settings=values)


@api_bp.get("/gallery")
def get_gallery():
    base_url = request.url_root.rstrip("/")
    images = GalleryImage.query.order_by(GalleryImage.uploaded_at.desc()).all()
    return jsonify(success=True, images=[img.to_dict(base_url) for img in images])


def _error(message, field=None, status=400):
    payload = {"success": False, "error": message}
    if field:
        payload["field"] = field
    return jsonify(payload), status


@api_bp.post("/bookings")
def create_booking():
    data = request.get_json(silent=True) or request.form

    full_name = (data.get("full_name") or "").strip()
    phone = (data.get("phone") or "").strip()
    booking_date_raw = (data.get("booking_date") or "").strip()
    shift = (data.get("shift") or "").strip()
    guests_count_raw = str(data.get("guests_count") or "").strip()
    notes = (data.get("notes") or "").strip()

    if not full_name or len(full_name) < 2:
        return _error("الرجاء إدخال الاسم الكامل.", "full_name")
    if len(full_name) > 120:
        return _error("الاسم طويل جداً.", "full_name")

    if not phone or len(phone) < 7 or not any(ch.isdigit() for ch in phone):
        return _error("الرجاء إدخال رقم هاتف صحيح.", "phone")
    if len(phone) > 30:
        return _error("رقم الهاتف طويل جداً.", "phone")

    if shift not in ("morning", "evening"):
        return _error("الرجاء اختيار نوع الشفت.", "shift")

    try:
        booking_date = datetime.strptime(booking_date_raw, "%Y-%m-%d").date()
    except ValueError:
        return _error("تاريخ الحجز غير صحيح.", "booking_date")
    if booking_date < date.today():
        return _error("لا يمكن اختيار تاريخ في الماضي.", "booking_date")

    try:
        guests_count = int(guests_count_raw)
    except ValueError:
        return _error("عدد الأشخاص غير صحيح.", "guests_count")
    if guests_count < 1 or guests_count > 100:
        return _error("عدد الأشخاص يجب أن يكون بين 1 و 100.", "guests_count")

    if len(notes) > 1000:
        return _error("الملاحظات طويلة جداً.", "notes")

    booking = Booking(
        booking_id=generate_booking_id(),
        full_name=full_name,
        phone=phone,
        booking_date=booking_date,
        shift=shift,
        guests_count=guests_count,
        notes=notes,
        status="new",
    )
    db.session.add(booking)
    db.session.commit()

    return jsonify(success=True, booking=booking.to_public_dict()), 201


@api_bp.get("/bookings/<booking_id>")
def check_booking_status(booking_id):
    """Let a guest check their booking status using booking_id + phone."""
    phone = (request.args.get("phone") or "").strip()
    if not phone:
        return _error("الرجاء إدخال رقم الهاتف المستخدم عند الحجز.", "phone")

    booking = Booking.query.filter_by(booking_id=booking_id.strip().upper()).first()
    if booking is None or booking.phone != phone:
        return _error("لم يتم العثور على حجز مطابق لهذه البيانات.", status=404)

    return jsonify(success=True, booking=booking.to_public_dict())
