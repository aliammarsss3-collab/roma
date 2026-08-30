/* منتجع رُومة — shared frontend behaviour */
(function () {
  "use strict";

  const API_BASE_URL = (window.RUMA_CONFIG && window.RUMA_CONFIG.API_BASE_URL) || "";

  /* ---------------------------- Sticky nav + toggle ---------------------------- */
  function initNav() {
    const header = document.querySelector(".site-header");
    const toggle = document.querySelector(".nav-toggle");
    const links = document.querySelector(".nav-links");

    if (header) {
      const onScroll = () => header.classList.toggle("scrolled", window.scrollY > 30);
      onScroll();
      window.addEventListener("scroll", onScroll, { passive: true });
    }

    if (toggle && links) {
      toggle.addEventListener("click", () => links.classList.toggle("open"));
      links.querySelectorAll("a").forEach((a) =>
        a.addEventListener("click", () => links.classList.remove("open"))
      );
    }
  }

  /* --------------------------------- Reveal on scroll --------------------------------- */
  function initReveal() {
    const items = document.querySelectorAll(".reveal");
    if (!items.length) return;

    if (!("IntersectionObserver" in window)) {
      items.forEach((el) => el.classList.add("in"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 }
    );
    items.forEach((el) => observer.observe(el));
  }

  /* ------------------------------- Load public settings ------------------------------- */
  function formatIQD(value) {
    const n = Number(value);
    if (Number.isNaN(n)) return value;
    return n.toLocaleString("ar-IQ");
  }

  async function loadSettings() {
    const targets = document.querySelectorAll("[data-setting]");
    const priceTargets = document.querySelectorAll("[data-price]");
    const serviceList = document.querySelector("[data-services]");
    if (!targets.length && !priceTargets.length && !serviceList) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/settings`);
      const data = await res.json();
      if (!data.success) return;
      const s = data.settings;

      targets.forEach((el) => {
        const key = el.getAttribute("data-setting");
        if (s[key]) el.textContent = s[key];
      });

      priceTargets.forEach((el) => {
        const key = el.getAttribute("data-price");
        if (s[key]) el.textContent = formatIQD(s[key]);
      });

      if (serviceList && Array.isArray(s.services) && s.services.length) {
        serviceList.innerHTML = "";
        const icons = ["🏊", "🌿", "🛋️", "🔒", "🚗", "🧹", "✨", "🌙"];
        s.services.forEach((service, i) => {
          const card = document.createElement("div");
          card.className = "service-card reveal";
          card.innerHTML = `<div class="dot">${icons[i % icons.length]}</div><h3>${service}</h3>`;
          serviceList.appendChild(card);
        });
        initReveal();
      }
    } catch (err) {
      // Backend not reachable yet (e.g. before deployment) — fail silently,
      // the page still works with its static default content.
      console.warn("تعذر تحميل الإعدادات من الخادم:", err);
    }
  }

  /* -------------------------------- Load public gallery -------------------------------- */
  async function loadGallery() {
    const grid = document.querySelector("[data-gallery]");
    if (!grid) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/gallery`);
      const data = await res.json();
      if (!data.success) return;

      if (!data.images.length) {
        grid.innerHTML = '<p class="gallery-empty">سيتم إضافة صور المعرض قريباً.</p>';
        return;
      }

      grid.innerHTML = "";
      data.images.forEach((img) => {
        const fig = document.createElement("figure");
        fig.innerHTML = `<img src="${img.url}" alt="${img.caption || "منتجع رُومة"}" loading="lazy">`;
        grid.appendChild(fig);
      });
    } catch (err) {
      grid.innerHTML = '<p class="gallery-empty">سيتم إضافة صور المعرض قريباً.</p>';
      console.warn("تعذر تحميل معرض الصور:", err);
    }
  }

  /* ----------------------------------- Booking form ----------------------------------- */
  function showAlert(box, type, message) {
    box.className = `alert alert-${type} show`;
    box.textContent = message;
  }

  function initBookingForm() {
    const form = document.querySelector("#booking-form");
    if (!form) return;

    const alertBox = form.querySelector(".alert");
    const submitBtn = form.querySelector('button[type="submit"]');
    const resultBox = document.querySelector("#booking-result");

    // Prevent selecting a past date in the date picker itself.
    const dateInput = form.querySelector('input[name="booking_date"]');
    if (dateInput) {
      const today = new Date().toISOString().slice(0, 10);
      dateInput.setAttribute("min", today);
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      alertBox.classList.remove("show");
      form.querySelectorAll(".field-error").forEach((el) => el.classList.remove("show"));

      const payload = {
        full_name: form.full_name.value.trim(),
        phone: form.phone.value.trim(),
        booking_date: form.booking_date.value,
        shift: form.shift.value,
        guests_count: form.guests_count.value,
        notes: form.notes.value.trim(),
      };

      submitBtn.disabled = true;
      submitBtn.textContent = "جارٍ الإرسال...";

      try {
        const res = await fetch(`${API_BASE_URL}/api/bookings`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();

        if (!res.ok || !data.success) {
          if (data.field) {
            const fieldError = form.querySelector(`[data-error-for="${data.field}"]`);
            if (fieldError) {
              fieldError.textContent = data.error;
              fieldError.classList.add("show");
            }
          }
          showAlert(alertBox, "danger", data.error || "حدث خطأ أثناء إرسال الحجز، الرجاء المحاولة مجدداً.");
          return;
        }

        form.reset();
        showAlert(alertBox, "success", "تم استلام طلب الحجز بنجاح! سنتواصل معكم لتأكيد الحجز.");
        if (resultBox) {
          resultBox.hidden = false;
          resultBox.querySelector("[data-booking-id]").textContent = data.booking.booking_id;
        }
      } catch (err) {
        showAlert(
          alertBox,
          "danger",
          "تعذر الاتصال بالخادم. تأكد من ضبط عنوان الخادم (API_BASE_URL) في ملف js/config.js."
        );
        console.error(err);
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "إرسال طلب الحجز";
      }
    });
  }

  /* ------------------------------- Booking status check -------------------------------- */
  function initStatusCheck() {
    const form = document.querySelector("#status-form");
    if (!form) return;
    const resultBox = document.querySelector("#status-result");

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const bookingId = form.booking_id.value.trim();
      const phone = form.phone.value.trim();

      resultBox.className = "alert show alert-success";
      resultBox.textContent = "جارٍ البحث...";

      try {
        const res = await fetch(
          `${API_BASE_URL}/api/bookings/${encodeURIComponent(bookingId)}?phone=${encodeURIComponent(phone)}`
        );
        const data = await res.json();

        if (!res.ok || !data.success) {
          resultBox.className = "alert show alert-danger";
          resultBox.textContent = data.error || "لم يتم العثور على الحجز.";
          return;
        }

        resultBox.className = "alert show alert-success";
        resultBox.innerHTML = `رقم الحجز <strong>${data.booking.booking_id}</strong> — الحالة الحالية: <strong>${data.booking.status_label}</strong>`;
      } catch (err) {
        resultBox.className = "alert show alert-danger";
        resultBox.textContent = "تعذر الاتصال بالخادم.";
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initNav();
    initReveal();
    loadSettings();
    loadGallery();
    initBookingForm();
    initStatusCheck();

    const yearEl = document.querySelector("[data-year]");
    if (yearEl) yearEl.textContent = new Date().getFullYear();
  });
})();
