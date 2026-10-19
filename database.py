"""
database.py - SQLite storage for Numerology AI.

Tables
  number_details          9 rows  (one per number 1-9)
  numerology_combinations 81 rows (Moolank x Bhagyank)
  readings                one row per user submission (photos optional; categories + photo_consent added by migrate())

The tables are created and filled automatically by init_db(), which app.py calls on start-up.
The content comes from data/numerology_data.json, so you can edit that file and delete
numerology.db to reload it.
"""
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "numerology.db"
DATA_FILE = BASE_DIR / "data" / "numerology_data.json"


class DatabaseError(Exception):
    """Raised for any database problem so the app can show a friendly message."""


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS number_details (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    number      INTEGER NOT NULL UNIQUE,
    planet      TEXT,
    title       TEXT,
    lucky_color TEXT,
    lucky_day   TEXT,
    personality TEXT,
    career      TEXT,
    love        TEXT,
    finance     TEXT,
    education   TEXT,
    strengths   TEXT,
    challenges  TEXT,
    remedies    TEXT
);

CREATE TABLE IF NOT EXISTS numerology_combinations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    moolank         INTEGER NOT NULL,
    bhagyank        INTEGER NOT NULL,
    personality     TEXT,
    career          TEXT,
    love            TEXT,
    marriage        TEXT,
    education       TEXT,
    finance         TEXT,
    strengths       TEXT,
    challenges      TEXT,
    compatibility   TEXT,
    remedies        TEXT,
    overall_summary TEXT,
    UNIQUE (moolank, bhagyank)
);

CREATE TABLE IF NOT EXISTS readings (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    gender        TEXT,
    dob           TEXT,
    tob           TEXT,
    pob           TEXT,
    mole_location TEXT,
    face_image    TEXT,
    palm_image    TEXT,
    moolank       INTEGER,
    bhagyank      INTEGER,
    ai_analysis   TEXT,
    paid          INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT
);
"""


# Columns added by the upgrade. Added with ALTER TABLE so existing databases and records are kept.
NEW_READING_COLUMNS = {
    "categories": "TEXT",                         # comma separated: love,growth,career,wellbeing (NULL on old records)
    "photo_consent": "INTEGER NOT NULL DEFAULT 0",  # 1 if the user ticked the Gemini photo consent box
}


def migrate(conn):
    """Safe schema update: only adds missing columns, never drops or recreates anything."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(readings)")}
    for column, ddl in NEW_READING_COLUMNS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE readings ADD COLUMN {column} {ddl}")


def init_db():
    """Create tables (if missing), migrate old ones, and load the numerology content (if empty)."""
    try:
        with get_connection() as conn:
            conn.executescript(SCHEMA)
            migrate(conn)
            seed_numerology_data(conn)
    except (sqlite3.Error, OSError, json.JSONDecodeError) as exc:
        raise DatabaseError(f"Could not initialise the database: {exc}") from exc


def seed_numerology_data(conn):
    have_numbers = conn.execute("SELECT COUNT(*) FROM number_details").fetchone()[0]
    have_combos = conn.execute("SELECT COUNT(*) FROM numerology_combinations").fetchone()[0]
    if have_numbers >= 9 and have_combos >= 81:
        return
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    for n in data["numbers"]:
        conn.execute(
            """INSERT OR IGNORE INTO number_details
               (number, planet, title, lucky_color, lucky_day, personality, career, love,
                finance, education, strengths, challenges, remedies)
               VALUES (:number, :planet, :title, :lucky_color, :lucky_day, :personality, :career,
                       :love, :finance, :education, :strengths, :challenges, :remedies)""", n)

    for c in data["combinations"]:
        conn.execute(
            """INSERT OR IGNORE INTO numerology_combinations
               (moolank, bhagyank, personality, career, love, marriage, education, finance,
                strengths, challenges, compatibility, remedies, overall_summary)
               VALUES (:moolank, :bhagyank, :personality, :career, :love, :marriage, :education,
                       :finance, :strengths, :challenges, :compatibility, :remedies, :overall_summary)""", c)


# ---------------------------------------------------------------- numerology lookups
def get_number_details(number):
    try:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM number_details WHERE number = ?", (number,)).fetchone()
        return dict(row) if row else None
    except sqlite3.Error as exc:
        raise DatabaseError(str(exc)) from exc


def get_combination(moolank, bhagyank):
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM numerology_combinations WHERE moolank = ? AND bhagyank = ?",
                (moolank, bhagyank)).fetchone()
        return dict(row) if row else None
    except sqlite3.Error as exc:
        raise DatabaseError(str(exc)) from exc


# ---------------------------------------------------------------- readings
def create_reading(name, gender, dob, tob, pob, mole_location, face_image, palm_image,
                   moolank, bhagyank, ai_analysis, categories=None, photo_consent=False):
    """Saves a reading and returns its id (a random, hard-to-guess string).
    face_image / palm_image may be None (photos are optional)."""
    reading_id = uuid.uuid4().hex
    try:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO readings
                   (id, name, gender, dob, tob, pob, mole_location, face_image, palm_image,
                    moolank, bhagyank, ai_analysis, paid, created_at, categories, photo_consent)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)""",
                (reading_id, name, gender, dob, tob, pob, mole_location, face_image or None, palm_image or None,
                 moolank, bhagyank, json.dumps(ai_analysis, ensure_ascii=False),
                 datetime.now().isoformat(timespec="seconds"),
                 ",".join(categories) if categories else None, 1 if photo_consent else 0))
        return reading_id
    except sqlite3.Error as exc:
        raise DatabaseError(str(exc)) from exc


def get_reading(reading_id):
    """Returns the reading as a dict (ai_analysis already decoded) or None."""
    if not reading_id or len(reading_id) != 32 or not all(c in "0123456789abcdef" for c in reading_id):
        return None
    try:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM readings WHERE id = ?", (reading_id,)).fetchone()
    except sqlite3.Error as exc:
        raise DatabaseError(str(exc)) from exc
    if row is None:
        return None
    reading = dict(row)
    try:
        reading["ai_analysis"] = json.loads(reading["ai_analysis"] or "{}")
    except json.JSONDecodeError:
        reading["ai_analysis"] = {}
    reading["paid"] = bool(reading["paid"])
    # Old records have no categories: treat that as "all categories" (see app.py).
    reading["categories"] = [c for c in (reading.get("categories") or "").split(",") if c]
    return reading


def mark_paid(reading_id):
    try:
        with get_connection() as conn:
            cur = conn.execute("UPDATE readings SET paid = 1 WHERE id = ?", (reading_id,))
        return cur.rowcount == 1
    except sqlite3.Error as exc:
        raise DatabaseError(str(exc)) from exc


def clear_photos(reading_id):
    """Forget the stored photo filenames of a reading (the caller deletes the files). Returns old names."""
    reading = get_reading(reading_id)
    if reading is None:
        return []
    try:
        with get_connection() as conn:
            conn.execute("UPDATE readings SET face_image = NULL, palm_image = NULL WHERE id = ?", (reading_id,))
    except sqlite3.Error as exc:
        raise DatabaseError(str(exc)) from exc
    return [n for n in (reading["face_image"], reading["palm_image"]) if n]


def delete_reading(reading_id):
    """Deletes the whole record. Returns the photo filenames so the caller can delete the files."""
    reading = get_reading(reading_id)
    if reading is None:
        return None
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM readings WHERE id = ?", (reading_id,))
    except sqlite3.Error as exc:
        raise DatabaseError(str(exc)) from exc
    return [n for n in (reading["face_image"], reading["palm_image"]) if n]


def expired_photo_rows(cutoff_iso):
    """Readings that still hold photos and were created before cutoff_iso."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT id FROM readings WHERE created_at < ?
                   AND ((face_image IS NOT NULL AND face_image != '') OR (palm_image IS NOT NULL AND palm_image != ''))""",
                (cutoff_iso,)).fetchall()
        return [r["id"] for r in rows]
    except sqlite3.Error as exc:
        raise DatabaseError(str(exc)) from exc


if __name__ == "__main__":
    init_db()
    print("Database ready:", DB_PATH)
