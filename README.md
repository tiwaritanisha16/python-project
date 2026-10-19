# Astro Buddy — Numerology & Vastu website

A Flask website with two services that share one design:

* **Numerology** — Personal Reading (free preview + complete report, optional face/palm photos), a **Core Numbers Calculator**
  (Life Path, Destiny, Soul Urge, Personality, Maturity, pinnacles, challenges, personal cycles, essence ...) and a **Number Guide**.
* **Vastu** — a **Vastu Meter** and a **Room-by-Room Guide** covering 33 rooms/elements across 8 directions.

Numerology and Vastu content comes from your two Excel workbooks (kept in `docs/source_data/`).
`Astro Buddy` is the brand name you chose; it has not been checked for trademark or domain availability. Change it with `SITE_NAME` in `.env`.

## Run on Windows (first time)
1. Extract the ZIP. Open the folder that contains `app.py` (the `astraveda` folder).
2. Open PowerShell in that folder (type `powershell` in the folder's address bar and press Enter).
3. Create and activate a virtual environment:
   ```
   py -m venv .venv
   .venv\Scripts\activate
   ```
   If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again.
4. Install the packages: `py -m pip install -r requirements.txt`
5. Create your settings file: `copy .env.example .env`, then edit `.env` in Notepad (see below).
6. Start the site: `py app.py`
7. Open **http://127.0.0.1:5000** in your browser. Stop the site with `Ctrl + C`.

Next time: open PowerShell in the folder, run `.venv\Scripts\activate`, then `py app.py`.

## Settings (`.env`)
| Setting | Purpose |
|---|---|
| `SITE_NAME` | Brand name shown on the site (default Astro Buddy) |
| `FLASK_SECRET_KEY` | Long random text (`py -c "import secrets; print(secrets.token_hex(32))"`) |
| `ASTROLOGER_NAME`, `ASTROLOGER_PHONE`, `ASTROBUDDY_URL`, `ASTROLOGER_INSTAGRAM_URL` | Contact details. Empty or `0001` shows a clear "not set yet / placeholder" label. URLs must start with `https://`. |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Only for the optional photo reflection in the Personal Reading. Everything else works without it. |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `REPORT_PRICE_INR`, `DEMO_PAYMENT_ENABLED` | Payment for the complete report. `true` = demo button, no money taken. |
| `PHOTO_RETENTION_DAYS` | Uploaded photos are removed after this many days (default 30). |

Do not put comments on the same line as a value.

## Run the tests
`py -m unittest discover -s tests -v`

## Project map
| Path | What it is |
|---|---|
| `app.py` | Flask routes, validation, preview/report building |
| `numerology.py`, `database.py`, `gemini_ai.py`, `content_extra.py` | Existing Personal Reading logic (Moolank/Bhagyank rules unchanged) |
| `numerology_core.py` | Core numbers calculations from the numerology workbook |
| `vastu.py` | Vastu lookup and meter from the Vastu workbook |
| `data/numerology_workbook.json`, `data/vastu_meter.json` | Workbook content as data (generated) |
| `data/numerology_data.json` | Number 1–9 profiles and 81 combinations (from your original project) |
| `tools/import_workbooks.py` | Rebuilds the two JSON files from the Excel files |
| `docs/` | Data import report, coverage report, editing guide, test report, source workbooks |
| `templates/`, `static/` | Pages, CSS, JavaScript, logo and your four photos (`static/img/photos/`) |
| `tests/` | Automated tests |

More: `docs/DATA_IMPORT_REPORT.md`, `docs/EDITING_GUIDE.md`, `docs/TEST_REPORT.md`.
