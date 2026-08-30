"""Admin panel: authentication + management of bookings, settings, gallery."""
import os
import uuid

from flask import (
    Blueprint, render_template, redirect, url_for, request, flash, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import User, Booking, Setting, GalleryImage, BOOKING_STATUSES

admin_bp = Blueprint("admin", __name__, template_folder="templates/admin")


def _allowed_image(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


# ---------------------------------------------------------------- Auth ----

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = User.query.filter_by(username=username).first()

        if user is not None and user.check_password(password):
            login_user(user, remember=False)
            flash("تم تسجيل الدخول بنجاح.", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("admin.dashboard"))

        flash("اسم المستخدم أو كلمة المرور غير صحيحة.", "danger")

    return render_template("admin/login.html")


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("تم تسجيل الخروج.", "success")
    return redirect(url_for("admin.login"))


# ----------------------------------------------------------- Dashboard ----

@admin_bp.route("/")
@login_required
def dashboard():
    counts = {
        status: Booking.query.filter_by(status=status).count()
        for status in BOOKING_STATUSES
    }
    total = Booking.query.count()
    recent = Booking.query.order_by(Booking.created_at.desc()).limit(6).all()
    return render_template("admin/dashboard.html", counts=counts, total=total, recent=recent,
                            statuses=BOOKING_STATUSES)


# ------------------------------------------------------------ Bookings ----

@admin_bp.route("/bookings")
@login_required
def bookings():
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()

    query = Booking.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Booking.full_name.ilike(like),
                Booking.phone.ilike(like),
                Booking.booking_id.ilike(like),
            )
        )
    if status in BOOKING_STATUSES:
        query = query.filter_by(status=status)

    items = query.order_by(Booking.created_at.desc()).all()
    return render_template(
        "admin/bookings.html", bookings=items, statuses=BOOKING_STATUSES, q=q, status=status
    )


@admin_bp.route("/bookings/<int:booking_id>")
@login_required
def booking_detail(booking_id):
    booking = db.session.get(Booking, booking_id)
    if booking is None:
        flash("لم يتم العثور على الحجز.", "danger")
        return redirect(url_for("admin.bookings"))
    return render_template("admin/booking_detail.html", booking=booking, statuses=BOOKING_STATUSES)


@admin_bp.route("/bookings/<int:booking_id>/status", methods=["POST"])
@login_required
def update_booking_status(booking_id):
    booking = db.session.get(Booking, booking_id)
    if booking is None:
        flash("لم يتم العثور على الحجز.", "danger")
        return redirect(url_for("admin.bookings"))

    new_status = request.form.get("status")
    if new_status not in BOOKING_STATUSES:
        flash("حالة غير صحيحة.", "danger")
    else:
        booking.status = new_status
        db.session.commit()
        flash(f"تم تحديث حالة الحجز إلى: {BOOKING_STATUSES[new_status]}", "success")

    return redirect(url_for("admin.booking_detail", booking_id=booking.id))


@admin_bp.route("/bookings/<int:booking_id>/delete", methods=["POST"])
@login_required
def delete_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if booking is not None:
        db.session.delete(booking)
        db.session.commit()
        flash("تم حذف الحجز.", "success")
    return redirect(url_for("admin.bookings"))


# ------------------------------------------------------------ Settings ----

SETTINGS_FIELDS = [
    ("resort_name_ar", "اسم المنتجع"),
    ("resort_tagline", "الشعار / الوصف القصير"),
    ("about_text", "نبذة عن المنتجع"),
    ("morning_price", "سعر الشفت الصباحي (دينار عراقي)"),
    ("evening_price", "سعر الشفت المسائي (دينار عراقي)"),
    ("morning_hours", "أوقات الشفت الصباحي"),
    ("evening_hours", "أوقات الشفت المسائي"),
    ("phone", "رقم الهاتف"),
    ("whatsapp", "رقم واتساب (بصيغة دولية بدون +)"),
    ("address", "العنوان"),
    ("services", "الخدمات (افصل بينها بعلامة |)"),
]


@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        for key, _label in SETTINGS_FIELDS:
            value = request.form.get(key, "").strip()
            Setting.set(key, value)
        flash("تم حفظ التغييرات بنجاح.", "success")
        return redirect(url_for("admin.settings"))

    values = {key: Setting.get(key, "") for key, _label in SETTINGS_FIELDS}
    return render_template("admin/settings.html", fields=SETTINGS_FIELDS, values=values)


# ------------------------------------------------------------- Gallery ----

@admin_bp.route("/gallery")
@login_required
def gallery():
    images = GalleryImage.query.order_by(GalleryImage.uploaded_at.desc()).all()
    return render_template("admin/gallery.html", images=images)


@admin_bp.route("/gallery/upload", methods=["POST"])
@login_required
def gallery_upload():
    file = request.files.get("image")
    caption = (request.form.get("caption") or "").strip()

    if file is None or file.filename == "":
        flash("الرجاء اختيار صورة.", "danger")
        return redirect(url_for("admin.gallery"))

    if not _allowed_image(file.filename):
        flash("صيغة الصورة غير مدعومة. الصيغ المسموحة: png, jpg, jpeg, webp", "danger")
        return redirect(url_for("admin.gallery"))

    safe_name = secure_filename(file.filename)
    ext = safe_name.rsplit(".", 1)[-1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    dest = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    file.save(dest)

    image = GalleryImage(filename=unique_name, caption=caption)
    db.session.add(image)
    db.session.commit()

    flash("تم رفع الصورة بنجاح.", "success")
    return redirect(url_for("admin.gallery"))


@admin_bp.route("/gallery/<int:image_id>/delete", methods=["POST"])
@login_required
def gallery_delete(image_id):
    image = db.session.get(GalleryImage, image_id)
    if image is not None:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], image.filename)
        if os.path.exists(path):
            os.remove(path)
        db.session.delete(image)
        db.session.commit()
        flash("تم حذف الصورة.", "success")
    return redirect(url_for("admin.gallery"))
