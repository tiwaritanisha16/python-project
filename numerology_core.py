"""
numerology_core.py - the "core numbers" calculations taken from Numerology_Numbers_and_Formulas.xls.

All tables (letter values, pinnacle ages, challenge themes, transit letters ...) are read from
data/numerology_workbook.json, which is generated from the workbook by tools/import_workbooks.py.
Nothing here is stored or sent anywhere: it is plain calculation.

Where the workbook is unclear or contradicts itself, the choice made here is listed in docs/DATA_IMPORT_REPORT.md
(section "Ambiguities and how they were handled").
"""
import json
import re
from datetime import date
from pathlib import Path

WB = json.loads((Path(__file__).parent / "data" / "numerology_workbook.json").read_text(encoding="utf-8"))
S1, S2 = WB["sheets"]["Sheet1"], WB["sheets"]["Sheet2"]
MASTERS = (11, 22, 33)
KARMIC = (13, 14, 16, 19)
SYSTEMS = {"pythagorean": "Pythagorean", "chaldean": "Chaldean"}
LETTER_VALUES = {"pythagorean": S1["pythagorean"]["values"], "chaldean": S1["chaldean"]["values"]}
CORE_TEXT = {c["title"]: c for c in S2["core_numbers"]}
TRANSIT = {}
for _row in S1["transit_letters"]["rows"]:
    _n = int(re.search(r"\d+", _row["number_label"]).group())
    for _ch in (x.upper() for x in re.findall(r"\b[A-Za-z]\b", _row["letters"])):   # the workbook has a lowercase 'k'
        TRANSIT[_ch] = (_n, _row["significance"])
PINNACLE_ROWS = {}
for _r in S1["pinnacle_table"]["rows"]:
    for _lp in re.findall(r"\d+", str(_r["life_path"])):
        PINNACLE_ROWS[int(_lp)] = _r
PINNACLE_SIG = {n: r["significance"] for n, r in PINNACLE_ROWS.items()}
MASTER_MEANING = {11: "Visionary, spiritual messenger", 22: "The Master Builder, practical manifestor",
                  33: "The Master Teacher-Healer, compassionate leader"}   # Sheet2 row 14, note cell I14
LIFE_ROWS = {int(r["life_path"]): r for r in S1["life_period"]["rows"]}


# ------------------------------------------------------------------ helpers
def digit_sum(n):
    return sum(int(d) for d in str(abs(int(n))))


def reduce_number(n, keep_master=True):
    """Reduce to one digit. With keep_master, 11 / 22 / 33 are kept (workbook rule)."""
    n = abs(int(n))
    while n > 9 and not (keep_master and n in MASTERS):
        n = digit_sum(n)
    return n


def reduce_text(n, keep_master=True):
    """'26 → 2+6 = 8' style description of a reduction."""
    n = abs(int(n))
    parts, cur = [], n
    while cur > 9 and not (keep_master and cur in MASTERS):
        parts.append("+".join(str(cur)) + f" = {digit_sum(cur)}")
        cur = digit_sum(cur)
    return " → ".join(parts) if parts else None


def shown(n):
    """Display of a number: master numbers show their root too (11/2)."""
    return f"{n}/{digit_sum(n)}" if n in MASTERS else str(n)


def base_digit(n):
    return reduce_number(n, keep_master=False)


def letters_of(text):
    return [c for c in (text or "").upper() if "A" <= c <= "Z"]


def words_of(name):
    return [w for w in re.split(r"[^A-Za-z]+", name or "") if w]


def letter_value(ch, system="pythagorean"):
    return LETTER_VALUES[system][ch]


def vowel_flags(word):
    """A E I O U are vowels. W and Y count as vowels when next to a vowel (the workbook's rule is worded as 'preceding
    letter'; its own VIDYA example treats Y as a vowel because an A follows, so a neighbouring vowel on either side is used)."""
    w, flags = word.upper(), []
    for i, ch in enumerate(w):
        if ch in "AEIOU":
            flags.append(True)
        elif ch in "WY":
            prev_v = i > 0 and w[i - 1] in "AEIOU"
            next_v = i + 1 < len(w) and w[i + 1] in "AEIOU"
            flags.append(prev_v or next_v)
        else:
            flags.append(False)
    return flags


def _word_sum(word, system, which):
    flags = vowel_flags(word)
    total, vals = 0, []
    for ch, is_v in zip(word.upper(), flags):
        v = letter_value(ch, system)
        take = which == "all" or (which == "vowel" and is_v) or (which == "consonant" and not is_v)
        vals.append(v if take else 0)
        total += v if take else 0
    return total, vals


def name_total(name, system, which):
    """Return (value, steps) for destiny (all), soul (vowel) or personality (consonant)."""
    words = words_of(name)
    steps, reduced = [], []
    for w in words:
        total, vals = _word_sum(w, system, which)
        r = reduce_number(total)
        steps.append(f"{w.upper()}: " + " ".join(str(v) for v in vals) + f"  → {total}" + (f" → {r}" if r != total else ""))
        reduced.append(r)
    grand = sum(reduced)
    final = reduce_number(grand)
    steps.append(f"Add the word totals: {' + '.join(map(str, reduced))} = {grand}" + (f" → {reduce_text(grand)}" if reduce_text(grand) else "")
                 + (f"  (master number {final})" if final in MASTERS else ""))
    return final, steps


def parse_date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


# ------------------------------------------------------------------ date based
def life_path(dob):
    d, m, y = reduce_number(dob.day), reduce_number(dob.month), reduce_number(dob.year)
    total = d + m + y
    v = reduce_number(total)
    steps = [f"Day {dob.day} → {d}", f"Month {dob.month} → {m}", f"Year {dob.year} → {y}" + (f"  ({reduce_text(dob.year)})" if reduce_text(dob.year) else ""),
             f"{d} + {m} + {y} = {total}" + (f" → {reduce_text(total)}" if reduce_text(total) else "")]
    return {"value": v, "steps": steps}


def birthday_number(dob):
    r = reduce_number(dob.day, keep_master=False)
    return {"value": dob.day, "reduced": r, "steps": [f"Day of the month = {dob.day}" + (f" → {reduce_text(dob.day, False)}" if dob.day > 9 else "")]}


def attitude_number(dob):
    s = dob.day + dob.month
    v = reduce_number(s)
    return {"value": v, "steps": [f"Day + Month = {dob.day} + {dob.month} = {s}" + (f" → {reduce_text(s)}" if reduce_text(s) else "")]}


def karmic_check(dob):
    s = dob.day + dob.month
    return {"value": s if s in KARMIC else None, "total": s,
            "steps": [f"Day + Month (not reduced) = {dob.day} + {dob.month} = {s}",
                      f"{s} is a karmic number (13, 14, 16 or 19)." if s in KARMIC else f"{s} is not 13, 14, 16 or 19, so no karmic number is present."]}


def relation(a, b):
    """Birthday-number modifier vs another number: the workbook's named lists plus its +/-/0 matrix."""
    order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33]
    if a not in order or b not in order:
        return None
    lo, hi = sorted((a, b), key=order.index)
    sym = S1["combination_matrix"]["cells"].get(f"{lo}-{hi}")
    lists = {"Fluctuating": [(1, 5), (6, 9), (2, 3)], "Discordant": [(4, 5), (8, 11), (6, 7)], "Harmonious": [(2, 6), (3, 6)]}
    named = [k for k, pairs in lists.items() if (lo, hi) in pairs]
    return {"pair": (lo, hi), "matrix_symbol": sym, "named": named}


# ------------------------------------------------------------------ name based
def intensified_absent(name):
    freq = {n: 0 for n in range(1, 10)}
    for ch in letters_of(name):
        freq[letter_value(ch, "pythagorean")] += 1
    top = max(freq.values()) if any(freq.values()) else 0
    intens = [n for n, c in freq.items() if c == top and top > 0]
    absent = [n for n, c in freq.items() if c == 0]
    return {"freq": freq, "intensified": intens, "absent": absent, "top_count": top}


def growth_number(name, system):
    words = words_of(name)
    if not words:
        return None
    first = words[0]
    total = sum(letter_value(c, system) for c in letters_of(first))
    v = reduce_number(total)
    return {"value": v, "steps": [f"{first.upper()}: " + "+".join(str(letter_value(c, system)) for c in letters_of(first)) + f" = {total}"
                                  + (f" → {reduce_text(total)}" if reduce_text(total) else "")]}


def habit_challenge(name):
    n = len(letters_of(name))
    v = reduce_number(n, keep_master=False)
    return {"value": v, "steps": [f"Letters in the full name = {n}" + (f" → {reduce_text(n, False)}" if n > 9 else "")]}


# ------------------------------------------------------------------ pinnacles / challenges
def _age_ranges(lp):
    row = PINNACLE_ROWS[base_digit(lp)]
    return [(row["p1_start"], row["p1_end"]), (row["p2_start"], row["p2_end"]), (row["p3_start"], row["p3_end"]),
            (row["p4_start"].rstrip("+") if isinstance(row["p4_start"], str) else row["p4_start"], None)]


def _range_text(r):
    return f"age {r[0]}+" if r[1] is None else f"age {r[0]}–{r[1]}"


def pinnacles(dob, lp, age):
    d, m, y = reduce_number(dob.day), reduce_number(dob.month), reduce_number(dob.year)
    p1 = reduce_number(m + d)
    p2 = reduce_number(d + y)
    p3 = reduce_number(p1 + p2)
    p4 = reduce_number(m + y)
    ranges = _age_ranges(lp)
    basis = [f"Month + Day = {m} + {d}", f"Day + Year = {d} + {y}", f"1st + 2nd = {p1} + {p2}", f"Month + Year = {m} + {y}"]
    items = []
    for i, (val, rng, b) in enumerate(zip((p1, p2, p3, p4), ranges, basis)):
        lo = int(rng[0])
        hi = rng[1]
        cur = age >= lo and (hi is None or age <= int(hi))
        items.append({"index": i + 1, "value": val, "age_text": _range_text(rng), "basis": b, "current": cur,
                      "meaning": PINNACLE_SIG.get(base_digit(val)) if val not in MASTERS else MASTER_MEANING[val]})
    return items


def challenges(dob, lp, age):
    d, m, y = reduce_number(dob.day), reduce_number(dob.month), reduce_number(dob.year)
    c1, c2 = abs(d - m), abs(d - y)
    c3, c4 = abs(c1 - c2), abs(m - y)
    ranges = _age_ranges(lp)
    basis = [f"|Day − Month| = |{d} − {m}|", f"|Day − Year| = |{d} − {y}|", f"|1st − 2nd| = |{c1} − {c2}|", f"|Month − Year| = |{m} − {y}|"]
    themes = S1["challenge_themes"]
    items = []
    for i, (val, rng, b) in enumerate(zip((c1, c2, c3, c4), ranges, basis)):
        lo, hi = int(rng[0]), rng[1]
        cur = age >= lo and (hi is None or age <= int(hi))
        items.append({"index": i + 1, "value": val, "age_text": _range_text(rng), "basis": b, "current": cur,
                      "theme": themes.get(str(val))})
    return items


def life_period(dob, lp):
    row = LIFE_ROWS[base_digit(lp)]
    return {"row": row, "month_number": reduce_number(dob.month), "day_number": reduce_number(dob.day), "year_number": reduce_number(dob.year)}


# ------------------------------------------------------------------ cycles
def personal_cycles(dob, today):
    a = reduce_number(dob.day + dob.month, keep_master=False)
    yr = reduce_number(today.year, keep_master=False)
    py = reduce_number(a + yr, keep_master=False)
    pm = reduce_number(py + today.month, keep_master=False)
    pd = reduce_number(pm + today.day, keep_master=False)
    uy = reduce_number(today.year, keep_master=False)
    um = reduce_number(uy + today.month, keep_master=False)
    ud = reduce_number(um + today.day, keep_master=False)
    return {
        "personal_year": {"value": py, "steps": [f"Day + Month = {dob.day} + {dob.month} → {a}", f"Year {today.year} → {yr}", f"{a} + {yr} → {py}"]},
        "personal_month": {"value": pm, "steps": [f"Personal Year {py} + month {today.month} = {py + today.month} → {pm}"]},
        "personal_day": {"value": pd, "steps": [f"Personal Month {pm} + day {today.day} = {pm + today.day} → {pd}"]},
        "universal_year": {"value": uy, "steps": [f"Digits of {today.year} → {uy}"]},
        "universal_month": {"value": um, "steps": [f"Universal Year {uy} + month {today.month} = {uy + today.month} → {um}"]},
        "universal_day": {"value": ud, "steps": [f"Universal Month {um} + day {today.day} = {um + today.day} → {ud}"]},
    }


# ------------------------------------------------------------------ essence
def _cycle_letter(word, age):
    """Letter active at a given age: each letter lasts as many years as its value, cycling through the word."""
    seq = []
    for ch in word.upper():
        seq += [(ch, letter_value(ch, "pythagorean"))] * letter_value(ch, "pythagorean")
    ch, v = seq[age % len(seq)]
    return ch, v


def essence(name, birth_year, year):
    words = words_of(name)
    if len(words) < 2 or year < birth_year:
        return None
    age = year - birth_year
    fl, fv = _cycle_letter(words[0], age)
    ll, lv = _cycle_letter(words[-1], age)
    total = fv + lv
    return {"year": year, "age": age, "first_letter": fl, "first_value": fv, "last_letter": ll, "last_value": lv,
            "total": total, "value": reduce_number(total)}


# ------------------------------------------------------------------ everything together
def full_report(name, dob, today, system="pythagorean"):
    dob, today = parse_date(dob), parse_date(today)
    if system not in SYSTEMS:
        system = "pythagorean"
    age = today.year - dob.year
    lp = life_path(dob)
    dest, dest_steps = name_total(name, system, "all")
    soul, soul_steps = name_total(name, system, "vowel")
    pers, pers_steps = name_total(name, system, "consonant")
    bday = birthday_number(dob)
    maturity_total = lp["value"] + dest
    ia = intensified_absent(name)
    cyc = personal_cycles(dob, today)
    ess = [essence(name, dob.year, today.year + k) for k in range(0, 5)]
    cur_ess = ess[0]
    r = {
        "system": system, "system_label": SYSTEMS[system], "age": age, "dob": dob, "today": today,
        "life_path": lp, "birthday": bday, "attitude": attitude_number(dob), "karmic": karmic_check(dob),
        "mulank": {"value": reduce_number(dob.day, keep_master=False), "compound": dob.day if dob.day > 9 else None},
        "destiny": {"value": dest, "steps": dest_steps}, "soul": {"value": soul, "steps": soul_steps},
        "personality": {"value": pers, "steps": pers_steps}, "growth": growth_number(name, system),
        "habit": habit_challenge(name),
        "maturity": {"value": reduce_number(maturity_total), "steps": [f"Life Path {lp['value']} + Destiny {dest} = {maturity_total}"
                                                                         + (f" → {reduce_text(maturity_total)}" if reduce_text(maturity_total) else "")]},
        "intensified": ia, "cycles": cyc, "pinnacles": pinnacles(dob, lp["value"], age),
        "challenges": challenges(dob, lp["value"], age), "life_period": life_period(dob, lp["value"]),
        "essence": ess, "relation": relation(lp["value"], reduce_number(dob.day)),
        "transit": None,
    }
    if cur_ess:
        r["transit"] = [{"letter": cur_ess["first_letter"], "number": TRANSIT[cur_ess["first_letter"]][0], "meaning": TRANSIT[cur_ess["first_letter"]][1]},
                        {"letter": cur_ess["last_letter"], "number": TRANSIT[cur_ess["last_letter"]][0], "meaning": TRANSIT[cur_ess["last_letter"]][1]}]
    return r


def about(title_part):
    """Workbook text (Sheet2) for a core number, found by part of its title."""
    for t, c in CORE_TEXT.items():
        if title_part.lower() in t.lower():
            return c
    return {}
