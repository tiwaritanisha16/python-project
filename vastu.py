"""
vastu.py - Vastu direction guide and Vastu Meter, built on data/vastu_meter.json (from Vastu_Meter_ContentV1.xls).

What the workbook contains: for each of 33 rooms / elements, a rating label and a score (1-10) for eight directions.
The centre (Brahmasthan) has a name in the workbook but no label or score, so it is shown as "not rated in the source".
The workbook contains NO formula. Looking up a room + direction returns exactly the workbook's label and score.
The overall "meter" (average of the scores you pick) is a simple presentation aid added by the website, not a workbook rule.
"""
import json
from pathlib import Path

DATA = json.loads((Path(__file__).parent / "data" / "vastu_meter.json").read_text(encoding="utf-8"))
DIRECTIONS = DATA["directions"]                      # code -> display name
RATED = ["NE", "E", "SE", "N", "S", "NW", "W", "SW"]  # directions that have scores
GRID = [["NW", "N", "NE"], ["W", "BR", "E"], ["SW", "S", "SE"]]   # compass layout, north at the top
ELEMENTS = {e["slug"]: e for e in DATA["elements"]}

# Grouping used only to make the long list easier to browse (the workbook has no such grouping).
GROUPS = [
    ("Entrances & outdoors", ["main-door", "porch", "verandah", "balcony", "open-space", "garden-lawn", "parking", "garage", "house-in-plot"]),
    ("Living spaces", ["living-room", "drawing-room", "dining-room", "guest-room", "kitchen", "master-bedroom", "children-s-bedroom"]),
    ("Work, study & wellbeing", ["study-room", "home-office", "pooja-room", "meditation-area", "gym-workout-area"]),
    ("Water & sanitation", ["well-or-underground-tank", "overhead-water-tank", "borewell-water-source", "septic-tank", "toilet-or-bathroom", "swimming-pool"]),
    ("Utility & structure", ["staircase", "lift-elevator", "store-room", "utility-room", "servant-room", "basement"]),
]


def grouped():
    seen, out = set(), []
    for title, slugs in GROUPS:
        items = [ELEMENTS[s] for s in slugs if s in ELEMENTS]
        seen.update(s for s in slugs if s in ELEMENTS)
        out.append((title, items))
    rest = [e for s, e in ELEMENTS.items() if s not in seen]
    if rest:
        out.append(("Other", rest))
    return out


def tone(score):
    """CSS tone for a score. Bands are for colouring only (the workbook defines no bands)."""
    if score is None:
        return "none"
    return "great" if score >= 9 else "good" if score >= 7 else "mid" if score >= 5 else "low"


def element(slug):
    return ELEMENTS.get(slug)


def lookup(slug, direction):
    e = ELEMENTS.get(slug)
    if not e or direction not in e["directions"]:
        return None
    d = e["directions"][direction]
    return {"element": e["name"], "direction": direction, "direction_name": d["direction_name"], "label": d["label"],
            "score": d["score"], "tone": tone(d["score"])}


def guide(slug):
    """Everything for one room: the 3x3 compass grid, best directions and ones to avoid (score order only)."""
    e = ELEMENTS.get(slug)
    if not e:
        return None
    cells = [[dict(e["directions"][c], code=c, tone=tone(e["directions"][c]["score"])) for c in row] for row in GRID]
    scored = [(c, e["directions"][c]) for c in RATED]
    top = max(d["score"] for _, d in scored)
    low = min(d["score"] for _, d in scored)
    return {"element": e, "grid": cells, "best": [(c, d) for c, d in scored if d["score"] == top],
            "weakest": [(c, d) for c, d in scored if d["score"] == low], "top": top, "low": low}


def meter(selections):
    """selections: {slug: direction_code}. Returns per-room results and the average score (out of 10 and as %).
    Unknown rooms/directions are reported in 'errors'; rooms placed in the centre are 'unrated'."""
    rows, errors, unrated = [], [], []
    for slug, code in selections.items():
        e = ELEMENTS.get(slug)
        if not e:
            errors.append(f"Unknown room: {slug}")
            continue
        if code not in DIRECTIONS:
            errors.append(f"Unknown direction for {e['name']}: {code}")
            continue
        d = e["directions"][code]
        if d["score"] is None:
            unrated.append(e["name"])
            continue
        best = max(e["directions"][c]["score"] for c in RATED)
        rows.append({"slug": slug, "name": e["name"], "direction": code, "direction_name": d["direction_name"], "label": d["label"],
                     "score": d["score"], "tone": tone(d["score"]), "best_score": best,
                     "best_dirs": [c for c in RATED if e["directions"][c]["score"] == best]})
    avg = round(sum(r["score"] for r in rows) / len(rows), 1) if rows else None
    return {"rows": rows, "average": avg, "percent": round(avg * 10) if avg is not None else None, "errors": errors, "unrated": unrated}
