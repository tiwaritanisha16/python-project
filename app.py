"""
Astro Buddy - Numerology & Vastu website
Run with:   py app.py      then open  http://127.0.0.1:5000
"""
import hmac
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import (Flask, abort, flash, jsonify, redirect, render_template, request,
                   send_from_directory, session, url_for)
from markupsafe import Markup, escape
from PIL import Image, ImageOps
from werkzeug.exceptions import HTTPException

import database
import gemini_ai
import numerology
import numerology_core as nc
import vastu
from content_extra import CATEGORIES, CATEGORY_KEYS, EXTRA, MOLE_NOTES
from site_content import FAQS

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_FILE_MB = 5
GENDERS = ["Male", "Female", "Other"]
MOLE_OPTIONS = ["Forehead", "Eyebrow", "Cheek", "Nose", "Chin", "Neck", "Hand", "Other", "No visible mole"]

SITE_NAME = os.getenv("SITE_NAME", "Astro Buddy").strip() or "Astro Buddy"
PHOTO_RETENTION_DAYS = int(os.getenv("PHOTO_RETENTION_DAYS", "30"))
NO_MOLE = "No mole information provided"
HAND_GUIDANCE = ("Hand Photo Guidance: Male users should upload their right-hand photo. "
                 "Female users should upload their left-hand photo.")

REPORT_PRICE_INR = int(os.getenv("REPORT_PRICE_INR", "199"))
DEMO_PAYMENT_ENABLED = os.getenv("DEMO_PAYMENT_ENABLED", "true").lower() in ("1", "true", "yes")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
app.config["MAX_CONTENT_LENGTH"] = 2 * MAX_FILE_MB * 1024 * 1024 + 1024 * 1024  # two images + form text

if app.secret_key == "dev-only-change-me":
    print("[startup] WARNING: FLASK_SECRET_KEY is not set in .env - set a long random value before going live.")

try:
    database.init_db()
except database.DatabaseError as exc:
    print(f"[startup] {exc}")


def safe_url(value):
    """Only real http(s) addresses become links; anything else (empty, a stray comment, javascript:) is ignored."""
    value = (value or "").strip()
    return value if re.match(r"^https?://[^\s<>\"']+$", value, re.IGNORECASE) else ""


def astro_settings():
    """AstroBuddy / astrologer details. All values come from .env so they are easy to replace later."""
    phone = os.getenv("ASTROLOGER_PHONE", "0001").strip() or "0001"
    return {
        "name": os.getenv("ASTROLOGER_NAME", "Dev").strip() or "Dev",
        "phone": phone,
        "phone_is_placeholder": phone == "0001",
        "phone_link": "tel:" + re.sub(r"[^\d+]", "", phone),
        "url": safe_url(os.getenv("ASTROBUDDY_URL", "")),
        "instagram": safe_url(os.getenv("ASTROLOGER_INSTAGRAM_URL", "")),
    }


NAV = [
    {"ep": "index", "label": "Home", "pages": ["home"]},
    {"ep": "numerology", "label": "Numerology", "pages": ["numerology", "reading_form", "categories", "numerology_calculator", "numerology_guide"],
     "children": [("reading_form", "Personal Reading"), ("categories", "Reading Topics"), ("numerology_calculator", "Core Numbers Calculator"), ("numerology_guide", "Number Guide")]},
    {"ep": "vastu", "label": "Vastu", "pages": ["vastu", "vastu_guide", "vastu_meter"],
     "children": [("vastu_meter", "Vastu Meter"), ("vastu_guide", "Room-by-Room Guide")]},
    {"ep": "how_it_works", "label": "How It Works", "pages": ["how_it_works"]},
    {"ep": "about", "label": "About Us", "pages": ["about"]},
    {"ep": "faq", "label": "FAQ", "pages": ["faq"]},
]


def brand_parts(name):
    """Splits the brand name into two parts so the wordmark can colour the second one gold (Astro|Buddy)."""
    if " " in name:
        first, rest = name.split(" ", 1)
        return first + " ", rest
    if name.lower().startswith("astro") and len(name) > 5:
        return name[:5], name[5:]
    return name, ""


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


def check_csrf():
    sent = request.form.get("csrf_token", "")
    if not sent or not hmac.compare_digest(sent, session.get("csrf", "")):
        abort(400, description="Your session expired. Please go back, refresh the page and try again.")


def payment_note():
    if razorpay_configured():
        return f"The complete report costs ₹{REPORT_PRICE_INR}, paid securely through Razorpay."
    if DEMO_PAYMENT_ENABLED:
        return "On this installation payment is a DEMO only: no money is taken and nothing is actually charged."
    return "Online payment is not available on this installation right now."


# =====================================================================================
# Template helpers
# =====================================================================================
@app.context_processor
def inject_globals():
    return {"price": REPORT_PRICE_INR, "year": datetime.now().year, "max_file_mb": MAX_FILE_MB,
            "gemini_ready": gemini_ai.is_configured(), "astro": astro_settings(), "nav": NAV, "site_name": SITE_NAME, "brand_parts": brand_parts(SITE_NAME),
            "csrf_token": csrf_token, "categories_all": CATEGORIES, "hand_guidance": HAND_GUIDANCE,
            "retention_days": PHOTO_RETENTION_DAYS, "demo_payment": DEMO_PAYMENT_ENABLED and not razorpay_configured()}


@app.after_request
def security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    if request.endpoint in ("preview", "report", "payment", "media"):
        resp.headers["Cache-Control"] = "private, no-store" if request.endpoint != "media" else resp.headers.get("Cache-Control", "private")
        resp.headers["X-Robots-Tag"] = "noindex"
    return resp


@app.template_filter("rich")
def rich_filter(text):
    """Turns plain AI/database text into safe HTML: paragraphs, '- ' bullets and **bold**."""
    if not text:
        return Markup("")
    html, bullets = [], []

    def inline(s):
        return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", str(escape(s)))

    def flush():
        if bullets:
            html.append("<ul>" + "".join(f"<li>{inline(b)}</li>" for b in bullets) + "</ul>")
            bullets.clear()

    for line in str(text).replace("\r", "").split("\n"):
        line = line.strip()
        if not line:
            flush()
            continue
        if re.match(r"^[-*•]\s+", line):
            bullets.append(re.sub(r"^[-*•]\s+", "", line))
        else:
            flush()
            plain = re.sub(r"^#+\s*", "", line)
            html.append("<p>" + inline(plain) + "</p>")
    flush()
    return Markup("".join(html))


def split_lines(text):
    return [ln.strip() for ln in (text or "").split("\n") if ln.strip()]


def first_sentences(text, count):
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return " ".join(parts[:count])


def render_error(title, message, status=400):
    return render_template("error.html", title=title, message=message, page="error"), status


# =====================================================================================
# Image handling
# =====================================================================================
def validate_upload(file, label):
    """Returns an error message or None."""
    if file is None or not file.filename:
        return None  # photos are optional: nothing uploaded is not an error
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return f"The {label} photo must be a PNG, JPG, JPEG or WEBP image."
    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    if size == 0:
        return f"The {label} photo appears to be empty."
    if size > MAX_FILE_MB * 1024 * 1024:
        return f"The {label} photo is larger than {MAX_FILE_MB} MB. Please choose a smaller image."
    return None


def save_image(file, kind):
    """Verifies the file is a real image, strips metadata, re-saves it as a JPEG with a random name."""
    try:
        probe = Image.open(file.stream)
        probe.verify()
        file.stream.seek(0)
        img = ImageOps.exif_transpose(Image.open(file.stream))
        img = img.convert("RGB")
        img.thumbnail((1600, 1600))
        filename = f"{uuid.uuid4().hex}_{kind}.jpg"
        img.save(UPLOAD_DIR / filename, "JPEG", quality=88)
        return filename
    except Exception:
        return None


def has_file(file):
    return file is not None and bool(file.filename)


def delete_uploads(*names):
    for n in names:
        if n:
            try:
                (UPLOAD_DIR / n).unlink(missing_ok=True)
            except OSError:
                pass


# =====================================================================================
# Form validation
# =====================================================================================
def validate_form(form, files):
    """Returns (clean, errors). Photos are optional; consent is required only when a photo is uploaded."""
    errors, clean = [], {}

    name = form.get("name", "").strip()
    if not name:
        errors.append("Please enter your full name.")
    elif len(name) > 80:
        errors.append("Your name is too long (80 characters maximum).")
    clean["name"] = name

    gender = form.get("gender", "").strip()
    if gender not in GENDERS:
        errors.append("Please select your gender.")
    clean["gender"] = gender

    dob_raw = form.get("dob", "").strip()
    try:
        clean["dob"] = numerology.parse_dob(dob_raw).isoformat() if dob_raw else None
        if not dob_raw:
            errors.append("Please enter your date of birth.")
    except ValueError as exc:
        clean["dob"] = None
        errors.append(str(exc))

    tob = form.get("tob", "").strip()
    if tob and not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", tob):
        errors.append("Please enter the time of birth as HH:MM.")
        tob = ""
    clean["tob"] = tob

    pob = form.get("pob", "").strip()
    if len(pob) > 100:
        errors.append("Place of birth is too long (100 characters maximum).")
        pob = pob[:100]
    clean["pob"] = pob

    chosen = [c for c in form.getlist("categories") if c in CATEGORY_KEYS]
    clean["categories"] = [c for c in CATEGORY_KEYS if c in chosen]  # keeps a stable order
    if not clean["categories"]:
        errors.append("Please choose at least one reading category.")

    mole = form.get("mole_location", "").strip()
    if mole and mole not in MOLE_OPTIONS:
        errors.append("Please choose a mole location from the list.")
        mole = ""
    mole_detail = form.get("mole_detail", "").strip()[:100]
    clean["mole_choice"], clean["mole_detail"] = mole, mole_detail
    if not mole or mole == "No visible mole":
        clean["mole_location"] = NO_MOLE
    else:
        clean["mole_location"] = mole + (f" ({mole_detail})" if mole_detail else "")

    palm_label = {"Male": "right-hand", "Female": "left-hand"}.get(gender, "hand")
    uploads = {}
    for key, label in (("face_image", "face"), ("palm_image", palm_label)):
        f = files.get(key)
        err = validate_upload(f, label)
        if err:
            errors.append(err)
        elif has_file(f):
            uploads[key] = f
    clean["consent"] = form.get("photo_consent") == "on"
    if uploads and not clean["consent"]:
        errors.append("To use a photo, please tick the box confirming it may be processed by Google Gemini AI. "
                      "Or simply remove the photo - it is optional.")
    clean["uploads"] = uploads
    return clean, errors


# =====================================================================================
# Preview + report building
# =====================================================================================
def selected_categories(reading):
    """Old records (before categories existed) show everything."""
    return reading["categories"] or list(CATEGORY_KEYS)


def category_titles(keys):
    return [(k, t, i) for k, t, i, _ in CATEGORIES if k in keys]


def pair(ex_m, ex_b, key):
    """Moolank + Bhagyank list items without repeats."""
    out = []
    for item in ex_m[key] + ex_b[key]:
        if item not in out:
            out.append(item)
    return out


def load_numbers(reading):
    m, b = reading["moolank"], reading["bhagyank"]
    md, bd = database.get_number_details(m), database.get_number_details(b)
    combo = database.get_combination(m, b)
    if not (md and bd and combo):
        raise database.DatabaseError("Numerology content is missing from the database.")
    return m, b, md, bd, combo


def combo_title(combo):
    summary = combo.get("overall_summary") or ""
    return summary.split(" - ", 1)[1].split(".", 1)[0] if " - " in summary else ""


def photo_state(reading):
    """What happened with the photos: dict of face/palm -> 'ok' | 'unavailable' | 'not_provided'."""
    ai = reading["ai_analysis"] or {}
    ok = ai.get("ai_available", False)  # old records only have this flag
    out = {}
    for kind in ("face", "palm"):
        out[kind] = ai.get(f"{kind}_status") or ("ok" if (ok and ai.get(f"{kind}_reading")) else "not_provided")
    return out, ai


def build_preview(reading):
    m, b, md, bd, combo = load_numbers(reading)
    ex_m, ex_b = EXTRA[m], EXTRA[b]
    cats = selected_categories(reading)
    insights = []
    if "love" in cats:
        insights.append({"key": "love", "title": "Love & Relationships", "icon": "♡",
                         "text": first_sentences(combo["love"], 2), "tip": pair(ex_m, ex_b, "love")[0]})
    if "growth" in cats:
        insights.append({"key": "growth", "title": "Personal Growth", "icon": "✦",
                         "text": first_sentences(md["personality"], 2), "tip": pair(ex_m, ex_b, "growth")[0]})
    if "career" in cats:
        insights.append({"key": "career", "title": "Career & Professional Life", "icon": "⚑",
                         "text": first_sentences(combo["career"], 2), "tip": ex_m["work"]})
    if "wellbeing" in cats:
        insights.append({"key": "wellbeing", "title": "General Wellbeing", "icon": "☾",
                         "text": "Traditionally, your numbers suggest steady routines and calm evenings help you feel balanced.",
                         "tip": pair(ex_m, ex_b, "routine")[0]})
    state, ai = photo_state(reading)
    summary = combo.get("overall_summary") or ""
    return {
        "reading": reading, "md": md, "bd": bd, "combo_title": combo_title(combo),
        "moolank_steps": numerology.explain_moolank(reading["dob"]),
        "bhagyank_steps": numerology.explain_bhagyank(reading["dob"]),
        "overview": " ".join(re.split(r"(?<=[.!?])\s+", summary)[1:3]) or first_sentences(combo["personality"], 2),
        "pair_text": first_sentences(combo["personality"], 3),
        "strengths": split_lines(combo["strengths"])[:4], "challenges": split_lines(combo["challenges"])[:3],
        "insights": insights, "reflection": ex_m["prompts"][0], "cats": category_titles(cats),
        "photo_state": state, "ai_summary": first_sentences(ai.get("overall_ai_summary", ""), 2),
        "ai_notice": ai.get("notice", ""),
    }


def core_numbers_card(r):
    """Compact 'core numbers' block for the full report. Steps for every number are on the calculator page."""
    kw = lambda n: (nc.MASTER_MEANING.get(n) or nc.PINNACLE_SIG.get(nc.base_digit(n), ""))
    cur_p = next((p for p in r["pinnacles"] if p["current"]), None)
    cur_c = next((c for c in r["challenges"] if c["current"]), None)
    lines = [f"Life Path Number: {nc.shown(r['life_path']['value'])} · {kw(r['life_path']['value'])}",
             f"Destiny / Expression Number: {nc.shown(r['destiny']['value'])} · {kw(r['destiny']['value'])}",
             f"Soul Urge Number: {nc.shown(r['soul']['value'])} · {kw(r['soul']['value'])}",
             f"Personality Number: {nc.shown(r['personality']['value'])} · {kw(r['personality']['value'])}",
             f"Birthday Number: {r['birthday']['value']} ({r['birthday']['reduced']})",
             f"Maturity Number: {nc.shown(r['maturity']['value'])} · {kw(r['maturity']['value'])}",
             "Karmic number: " + (f"{r['karmic']['value']} is present" if r["karmic"]["value"] else "none present (day + month is not 13, 14, 16 or 19)"),
             f"Personal Year {r['today'].year}: {r['cycles']['personal_year']['value']} · {kw(r['cycles']['personal_year']['value'])}"]
    blocks = [{"bullets": lines}]
    cyc = []
    if cur_p:
        cyc.append(f"Current pinnacle: {cur_p['value']} ({cur_p['age_text']}) · {cur_p['meaning']}")
    if cur_c:
        cyc.append(f"Current challenge: {cur_c['value']} ({cur_c['age_text']}) · {cur_c['theme']}")
    if cyc:
        blocks.append({"label": "Where you are in your life cycles", "bullets": cyc})
    blocks.append({"text": "These come from the Numerology Number Guide formulas (Pythagorean letter values). "
                           "Open the Core Numbers Calculator to see every calculation step and your full pinnacle and challenge cycles."})
    return {"key": "core", "title": "Your Core Numbers", "icon": "∞", "blocks": blocks}


def build_report(reading):
    """Combines database content, extra reflection content and (optional) Gemini output."""
    m, b, md, bd, combo = load_numbers(reading)
    ex_m, ex_b = EXTRA[m], EXTRA[b]
    cats = selected_categories(reading)
    state, ai = photo_state(reading)

    def lucky(d):
        return f"Colours: {d['lucky_color']}  |  Day: {d['lucky_day']}"

    sections = {}
    sections["love"] = [
        {"label": "Traditional interpretation", "text": combo["love"]},
        {"label": "Marriage tendencies", "text": combo["marriage"]},
        {"label": "Compatibility", "text": combo["compatibility"]},
        {"label": "Communication & relationship reflection", "bullets": pair(ex_m, ex_b, "love")},
        {"label": "Possible strengths", "bullets": split_lines(combo["strengths"])[:3]},
        {"label": "Possible challenges", "bullets": split_lines(combo["challenges"])[:3]},
        {"label": "Reflection prompts", "bullets": ex_m["prompts"][1:] + ex_b["prompts"][1:2]},
    ]
    sections["growth"] = [
        {"label": "Personality themes", "text": combo["personality"]},
        {"label": f"Moolank {m} - {md['title']}", "text": md["personality"]},
        {"label": f"Bhagyank {b} - {bd['title']}", "text": bd["personality"]},
        {"label": "Strengths", "bullets": split_lines(combo["strengths"])},
        {"label": "Areas for improvement", "bullets": split_lines(combo["challenges"])},
        {"label": "Self-reflection prompts", "bullets": pair(ex_m, ex_b, "prompts")},
        {"label": "Practical growth suggestions", "bullets": pair(ex_m, ex_b, "growth")},
    ]
    sections["career"] = [
        {"label": "Traditional career themes", "text": combo["career"]},
        {"label": f"Moolank {m} traditionally", "text": md["career"]},
        {"label": f"Bhagyank {b} traditionally", "text": bd["career"]},
        {"label": "Work-style reflection", "text": ex_m["work"] + ("" if ex_b["work"] == ex_m["work"] else " " + ex_b["work"])},
        {"label": "Education & learning", "text": combo["education"]},
        {"label": "Money habits (traditional view)", "text": combo["finance"]},
        {"label": "Skills and habits to develop", "bullets": pair(ex_m, ex_b, "skills")},
    ]
    sections["wellbeing"] = [
        {"label": "General lifestyle reflection", "text": "These are gentle lifestyle ideas drawn from traditional numerology themes. "
                                                       "They are not medical advice and say nothing about your health."},
        {"label": "Healthy routine ideas", "bullets": pair(ex_m, ex_b, "routine")},
        {"label": "Stress-management suggestions", "bullets": pair(ex_m, ex_b, "stress")},
        {"label": "Self-care prompts", "bullets": pair(ex_m, ex_b, "selfcare")},
    ]
    for key in sections:  # drop empty blocks
        sections[key] = [blk for blk in sections[key] if blk.get("text") or blk.get("bullets")]

    chosen = [{"key": k, "title": t, "icon": i, "blocks": sections[k]} for k, t, i, _ in CATEGORIES if k in cats]
    skipped = [t for k, t, i, _ in CATEGORIES if k not in cats]

    extras = [{"key": "remedies", "title": "Traditional Remedies", "icon": "🪔", "blocks": [
        {"bullets": split_lines(combo["remedies"])},
        {"label": f"Moolank {m} remedies", "bullets": split_lines(md["remedies"])},
        {"label": f"Bhagyank {b} remedies", "bullets": split_lines(bd["remedies"])},
        {"label": "Lucky colours & days", "text": f"Moolank {m}: {lucky(md)}\nBhagyank {b}: {lucky(bd)}"}]}]
    try:
        core = nc.full_report(reading["name"], reading["dob"], datetime.now().date())
        extras.insert(0, core_numbers_card(core))
    except Exception as exc:  # never break the report because of the optional core-number section
        print(f"[report] core numbers skipped: {type(exc).__name__}")
    mole_key = (reading["mole_location"] or NO_MOLE)
    if mole_key != NO_MOLE:
        base = mole_key.split(" (")[0]
        extras.append({"key": "mole", "title": "Mole Reading (traditional)", "icon": "◉", "blocks": [
            {"label": f"Location you entered: {mole_key}", "text": MOLE_NOTES.get(base, MOLE_NOTES["Other"])
             + " This is a traditional note only, and not a statement about your health."}]})

    summary_blocks = [{"text": combo["overall_summary"]}]
    if state["face"] == "ok" or state["palm"] == "ok":
        summary_blocks.append({"label": "AI-assisted summary (Gemini, speculative)", "text": ai.get("overall_ai_summary", "")})

    return {
        "reading": reading, "moolank_details": md, "bhagyank_details": bd, "combo": combo, "combo_title": combo_title(combo),
        "moolank_steps": numerology.explain_moolank(reading["dob"]),
        "bhagyank_steps": numerology.explain_bhagyank(reading["dob"]),
        "chosen": chosen, "skipped": skipped, "extras": extras, "summary_blocks": summary_blocks,
        "photo_state": state, "ai": ai, "ai_notice": ai.get("notice", ""),
        "disclaimer": ai.get("disclaimer") or gemini_ai.DISCLAIMER,
        "copy_text": f"{reading['name']} - Moolank {m}, Bhagyank {b}: {combo['overall_summary']}",
    }


# =====================================================================================
# Photo retention
# =====================================================================================
def purge_expired_photos():
    """Removes photos older than PHOTO_RETENTION_DAYS (the reading text itself is kept). Runs on start-up and
    after every new submission - the site has no background scheduler."""
    if PHOTO_RETENTION_DAYS <= 0:
        return 0
    cutoff = (datetime.now() - timedelta(days=PHOTO_RETENTION_DAYS)).isoformat(timespec="seconds")
    count = 0
    try:
        for rid in database.expired_photo_rows(cutoff):
            delete_uploads(*database.clear_photos(rid))
            count += 1
    except database.DatabaseError as exc:
        print(f"[retention] {exc}")
    return count


purge_expired_photos()


# =====================================================================================
# Routes - public pages
# =====================================================================================
def faq_items():
    return [(q, a.format(days=PHOTO_RETENTION_DAYS, payment_note=payment_note())) for q, a in FAQS]


@app.get("/")
def index():
    """Simple landing page: two entrances (Numerology, Vastu) into the existing sections."""
    return render_template("index.html", page="home")


@app.get("/about")
def about():
    return render_template("about.html", page="about")


@app.get("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html", page="how_it_works")


@app.get("/categories")
def categories():
    return render_template("categories.html", page="categories")


@app.get("/faq")
def faq():
    return render_template("faq.html", faqs=faq_items(), page="faq")


@app.get("/contact")
def contact():
    return render_template("contact.html", page="contact")


@app.get("/privacy")
def privacy():
    return render_template("privacy.html", page="privacy", payment_note=payment_note())


@app.get("/terms")
def terms():
    return render_template("terms.html", page="terms", payment_note=payment_note())


# =====================================================================================
# Routes - Numerology tools (workbook based, nothing is stored)
# =====================================================================================
NUM_ABOUT = {k: nc.about(v) for k, v in {
    "life_path": "Life Path", "destiny": "Destiny", "soul": "Soul", "personality": "Personality", "birthday": "Birthday",
    "intensified": "Intensified", "absent": "Absent", "growth": "Growth", "habit": "Habit", "maturity": "Maturity",
    "karmic": "Karmic", "personal_year": "Personal / Universal", "personal_month": "Personal Month", "personal_day": "Personal Day",
    "life_period": "Life Path Period", "pinnacle": "Pinnacle", "challenge": "Challenge", "essence": "Essence", "transit": "Transit"}.items()}


@app.get("/numerology", endpoint="numerology")
def numerology_home():
    numbers = [dict(database.get_number_details(n), number=n) for n in range(1, 10)]
    return render_template("numerology.html", numbers=numbers, page="numerology")


def validate_calc(form):
    errors, clean = [], {}
    name = form.get("name", "").strip()
    if not nc.letters_of(name):
        errors.append("Please enter your full name using English (A-Z) letters. The workbook's letter tables are for those letters.")
    elif len(name) > 80:
        errors.append("The name is too long (80 characters maximum).")
    clean["name"] = name
    try:
        dob = nc.parse_date(form.get("dob", "").strip())
        if dob.year < 1900 or dob > datetime.now().date():
            raise ValueError
        clean["dob"] = dob
    except (ValueError, TypeError):
        errors.append("Please enter a valid date of birth (between 1900 and today).")
    as_of = form.get("as_of", "").strip()
    try:
        clean["as_of"] = nc.parse_date(as_of) if as_of else datetime.now().date()
        if not 1900 <= clean["as_of"].year <= 2100:
            raise ValueError
    except (ValueError, TypeError):
        errors.append("Please enter a valid 'calculate for' date.")
        clean["as_of"] = datetime.now().date()
    if "dob" in clean and clean["as_of"] < clean["dob"]:
        errors.append("The 'calculate for' date cannot be before the date of birth.")
    system = form.get("system", "pythagorean")
    clean["system"] = system if system in nc.SYSTEMS else "pythagorean"
    return clean, errors


@app.route("/numerology/calculator", methods=["GET", "POST"])
def numerology_calculator():
    ctx = dict(page="numerology_calculator", form=request.form if request.method == "POST" else {}, result=None,
               systems=nc.SYSTEMS, about=NUM_ABOUT, nc=nc, today=datetime.now().date().isoformat())
    if request.method == "POST":
        check_csrf()
        clean, errors = validate_calc(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("numerology_calculator.html", **ctx), 400
        ctx["result"] = nc.full_report(clean["name"], clean["dob"], clean["as_of"], clean["system"])
        ctx["name"] = clean["name"]
    return render_template("numerology_calculator.html", **ctx)


@app.get("/numerology/guide")
def numerology_guide():
    return render_template("numerology_guide.html", page="numerology_guide", nc=nc, wb=nc.WB["sheets"],
                           numbers=[dict(database.get_number_details(n), number=n) for n in range(1, 10)])


# =====================================================================================
# Routes - Vastu tools (workbook based, nothing is stored)
# =====================================================================================
@app.get("/vastu", endpoint="vastu")
def vastu_home():
    return render_template("vastu.html", page="vastu", groups=vastu.grouped(), count=len(vastu.ELEMENTS),
                           sample=vastu.guide("main-door"))


@app.get("/vastu/guide")
def vastu_guide():
    return render_template("vastu_guide.html", page="vastu_guide", groups=vastu.grouped())


@app.get("/vastu/guide/<slug>")
def vastu_element(slug):
    g = vastu.guide(slug)
    if g is None:
        abort(404)
    names = list(vastu.ELEMENTS)
    i = names.index(slug)
    return render_template("vastu_element.html", page="vastu_guide", g=g, dirs=vastu.DIRECTIONS,
                           prev=vastu.ELEMENTS[names[i - 1]], nxt=vastu.ELEMENTS[names[(i + 1) % len(names)]])


@app.get("/vastu/meter")
def vastu_meter():
    picks = {slug: request.args.get(slug, "").strip() for slug in vastu.ELEMENTS if request.args.get(slug, "").strip()}
    result, submitted = None, "go" in request.args
    if submitted:
        if not picks:
            flash("Choose a direction for at least one room, then calculate.", "error")
        else:
            result = vastu.meter(picks)
    return render_template("vastu_meter.html", page="vastu_meter", groups=vastu.grouped(), picks=picks, result=result,
                           rated=vastu.RATED, dirs=vastu.DIRECTIONS), (400 if submitted and not picks else 200)


# =====================================================================================
# Routes - the reading flow
# =====================================================================================
def render_form(form, status=200):
    preselect = form.getlist("categories") if hasattr(form, "getlist") else []
    if not preselect and not form.get("name") and request.args.get("cat") in CATEGORY_KEYS:
        preselect = [request.args["cat"]]
    if not preselect and not form.get("name"):
        preselect = list(CATEGORY_KEYS)
    return render_template("reading.html", form=form, genders=GENDERS, mole_options=MOLE_OPTIONS,
                           selected=preselect, page="reading_form", scroll_to_errors=status != 200), status


@app.route("/reading", methods=["GET", "POST"])
def reading_form():
    if request.method == "GET":
        return render_form({})

    check_csrf()
    clean, errors = validate_form(request.form, request.files)
    if errors:
        for e in errors:
            flash(e, "error")
        return render_form(request.form, 400)

    face_name = palm_name = None
    if "face_image" in clean["uploads"]:
        face_name = save_image(clean["uploads"]["face_image"], "face")
    if "palm_image" in clean["uploads"]:
        palm_name = save_image(clean["uploads"]["palm_image"], "palm")
    unreadable = ("face_image" in clean["uploads"] and not face_name) or ("palm_image" in clean["uploads"] and not palm_name)
    if unreadable:
        delete_uploads(face_name, palm_name)
        flash("One of the images could not be read as a picture. Please choose a valid PNG, JPG or WEBP file, or remove it - photos are optional.", "error")
        return render_form(request.form, 400)

    try:
        numbers = numerology.calculate_numbers(clean["dob"])
        # Gemini is only contacted when there is at least one consented photo.
        ai = gemini_ai.analyze_images(UPLOAD_DIR / face_name if face_name else None,
                                      UPLOAD_DIR / palm_name if palm_name else None, clean["gender"])
        reading_id = database.create_reading(
            clean["name"], clean["gender"], clean["dob"], clean["tob"], clean["pob"], clean["mole_location"],
            face_name, palm_name, numbers["moolank"], numbers["bhagyank"], ai,
            categories=clean["categories"], photo_consent=bool(face_name or palm_name) and clean["consent"])
    except database.DatabaseError:
        delete_uploads(face_name, palm_name)
        return render_error("Something went wrong",
                            "We could not save your reading just now. Please try again in a moment.", 500)
    purge_expired_photos()
    return redirect(url_for("preview", reading_id=reading_id))


def load_reading_or_404(reading_id):
    try:
        reading = database.get_reading(reading_id)
    except database.DatabaseError:
        abort(500)
    if reading is None:
        abort(404)
    return reading


@app.get("/preview/<reading_id>")
def preview(reading_id):
    reading = load_reading_or_404(reading_id)
    if reading["paid"]:
        return redirect(url_for("report", reading_id=reading_id))
    try:
        data = build_preview(reading)
    except database.DatabaseError:
        abort(500)
    return render_template("preview.html", payment_text=payment_note(), page="reading_form", **data)


@app.get("/payment/<reading_id>")
def payment(reading_id):
    reading = load_reading_or_404(reading_id)
    if reading["paid"]:
        return redirect(url_for("report", reading_id=reading_id))
    return render_template("payment.html", reading=reading, demo_enabled=DEMO_PAYMENT_ENABLED,
                           razorpay_ready=razorpay_configured(), page="reading_form",
                           razorpay_key=os.getenv("RAZORPAY_KEY_ID", ""))


@app.get("/report/<reading_id>")
def report(reading_id):
    reading = load_reading_or_404(reading_id)
    if not reading["paid"]:
        flash("Please unlock your reading to view the complete report.", "info")
        return redirect(url_for("payment", reading_id=reading_id))
    try:
        data = build_report(reading)
    except database.DatabaseError:
        abort(500)
    return render_template("report.html", page="reading_form", **data)


@app.get("/media/<reading_id>/<kind>")
def media(reading_id, kind):
    """Serves an uploaded photo. The reading id is a long random value, so only the owner has the link."""
    if kind not in ("face", "palm"):
        abort(404)
    reading = load_reading_or_404(reading_id)
    filename = reading["face_image"] if kind == "face" else reading["palm_image"]
    if not filename:
        abort(404)
    resp = send_from_directory(UPLOAD_DIR, filename)
    resp.headers["Cache-Control"] = "private, max-age=3600"
    return resp


@app.post("/reading/<reading_id>/delete-photos")
def delete_photos(reading_id):
    check_csrf()
    load_reading_or_404(reading_id)
    try:
        delete_uploads(*database.clear_photos(reading_id))
    except database.DatabaseError:
        return render_error("Could not delete", "We could not remove your photos just now. Please try again.", 500)
    flash("Your uploaded photos were deleted from this website's storage.", "success")
    return redirect(request.referrer or url_for("preview", reading_id=reading_id))


@app.post("/reading/<reading_id>/delete")
def delete_reading(reading_id):
    check_csrf()
    load_reading_or_404(reading_id)
    try:
        names = database.delete_reading(reading_id) or []
        delete_uploads(*names)
    except database.DatabaseError:
        return render_error("Could not delete", "We could not delete your reading just now. Please try again.", 500)
    flash("Your reading and any uploaded photos were deleted.", "success")
    return redirect(url_for("index"))


# ---------------------------------------------------------------- DEMO payment (local testing only)
@app.get("/demo-payment/<reading_id>")
def demo_payment(reading_id):
    """DEMO PAYMENT - no money is involved. It only marks the reading as unlocked so you can test the flow."""
    if not DEMO_PAYMENT_ENABLED:
        return render_error("Demo payment is turned off",
                            "This site is not running in demo mode. Please use the real payment option.", 403)
    reading = load_reading_or_404(reading_id)
    try:
        database.mark_paid(reading["id"])
    except database.DatabaseError:
        return render_error("Payment problem", "We could not unlock your reading. Please try again.", 500)
    flash("DEMO payment simulated - no real money was charged. Your reading is unlocked.", "success")
    return redirect(url_for("report", reading_id=reading_id))


# ---------------------------------------------------------------- Razorpay (ready for real payments)
def razorpay_configured():
    key_id, secret = os.getenv("RAZORPAY_KEY_ID", ""), os.getenv("RAZORPAY_KEY_SECRET", "")
    return bool(key_id and secret and key_id != "your_key_id" and secret != "your_key_secret")


def get_razorpay_client():
    import razorpay  # imported here so the app still runs if the package is missing
    return razorpay.Client(auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET")))


@app.post("/payment/create-order/<reading_id>")
def create_order(reading_id):
    reading = load_reading_or_404(reading_id)
    if not razorpay_configured():
        return jsonify(error="Online payments are not enabled yet."), 400
    try:
        order = get_razorpay_client().order.create({
            "amount": REPORT_PRICE_INR * 100, "currency": "INR", "receipt": reading["id"][:30],
            "notes": {"reading_id": reading["id"]}})
    except Exception as exc:
        print(f"[razorpay] order creation failed: {exc}")
        return jsonify(error="We could not start the payment. Please try again."), 502
    session[f"order_{reading['id']}"] = order["id"]
    return jsonify(order_id=order["id"], amount=order["amount"], currency="INR",
                   key_id=os.getenv("RAZORPAY_KEY_ID"), name=reading["name"])


@app.post("/payment/verify/<reading_id>")
def verify_payment(reading_id):
    reading = load_reading_or_404(reading_id)
    payload = request.get_json(silent=True) or {}
    order_id = payload.get("razorpay_order_id", "")
    if not razorpay_configured() or not hmac.compare_digest(str(order_id), str(session.get(f"order_{reading['id']}", ""))):
        return jsonify(error="Payment could not be verified."), 400
    try:
        get_razorpay_client().utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payload.get("razorpay_payment_id", ""),
            "razorpay_signature": payload.get("razorpay_signature", "")})
        database.mark_paid(reading["id"])
    except Exception as exc:
        print(f"[razorpay] verification failed: {exc}")
        return jsonify(error="Payment verification failed. If money was deducted, please contact support."), 400
    return jsonify(redirect=url_for("report", reading_id=reading["id"]))


# =====================================================================================
# Friendly error pages (users never see a Python traceback)
# =====================================================================================
@app.errorhandler(Exception)
def handle_any_error(exc):
    if isinstance(exc, HTTPException):
        messages = {
            404: ("Page not found", "We could not find what you were looking for. The link may be wrong or expired."),
            413: ("Files too large", f"Each photo must be under {MAX_FILE_MB} MB. Please choose smaller images."),
            405: ("Not allowed", "That action is not available on this page."),
            400: ("Please try again", exc.description or "That request could not be processed."),
        }
        title, msg = messages.get(exc.code, ("Something went wrong", exc.description or "Please try again."))
        return render_error(title, msg, exc.code)
    print(f"[error] {type(exc).__name__}: {exc}")
    return render_error("Something went wrong", "An unexpected problem occurred. Please try again in a moment.", 500)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=os.getenv("FLASK_DEBUG", "0") == "1")
