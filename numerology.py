"""
numerology.py - Traditional Indian numerology calculations.

Moolank  (Birth Number)   : day of birth reduced to a single digit (1-9)
Bhagyank (Destiny Number) : all digits of the full date of birth added and reduced to 1-9

Example: 16/07/2002
    Moolank  = 1 + 6                         = 7
    Bhagyank = 1+6+0+7+2+0+0+2 = 18 -> 1+8   = 9
"""
from datetime import date, datetime


def parse_dob(dob):
    """Accepts a date object, 'YYYY-MM-DD' or 'DD/MM/YYYY' (also DD-MM-YYYY). Returns a date.
    Raises ValueError if the date is invalid, in the future, or before 1900."""
    if isinstance(dob, datetime):
        parsed = dob.date()
    elif isinstance(dob, date):
        parsed = dob
    else:
        text = str(dob or "").strip()
        parsed = None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                parsed = datetime.strptime(text, fmt).date()
                break
            except ValueError:
                continue
        if parsed is None:
            raise ValueError("Please enter a valid date of birth.")
    if parsed.year < 1900 or parsed > date.today():
        raise ValueError("Please enter a realistic date of birth (between 1900 and today).")
    return parsed


def reduce_to_single_digit(number):
    """Keep adding the digits until only one digit (1-9) remains."""
    number = abs(int(number))
    while number > 9:
        number = sum(int(d) for d in str(number))
    return number


def calculate_moolank(dob):
    """Birth number: the day of the month reduced to one digit."""
    return reduce_to_single_digit(parse_dob(dob).day)


def calculate_bhagyank(dob):
    """Destiny number: every digit of day + month + year added, then reduced."""
    parsed = parse_dob(dob)
    digits = f"{parsed.day:02d}{parsed.month:02d}{parsed.year:04d}"
    return reduce_to_single_digit(sum(int(d) for d in digits))


def calculate_numbers(dob):
    """Returns {'moolank': x, 'bhagyank': y}"""
    return {"moolank": calculate_moolank(dob), "bhagyank": calculate_bhagyank(dob)}


if __name__ == "__main__":
    print(calculate_numbers("2002-07-16"))   # {'moolank': 7, 'bhagyank': 9}


# ---------------------------------------------------------------- calculation steps (added in the upgrade)
# The calculation RULES above are unchanged. These helpers only describe them in words for the report.
def _reduce_steps(number):
    """'18 -> 1+8 = 9' style text for one reduction chain."""
    number = abs(int(number))
    parts = []
    while number > 9:
        digits = [int(d) for d in str(number)]
        parts.append(f"{'+'.join(map(str, digits))} = {sum(digits)}")
        number = sum(digits)
    return parts


def explain_moolank(dob):
    parsed = parse_dob(dob)
    day = parsed.day
    chain = _reduce_steps(day)
    if not chain:
        return f"Day of birth {day} is already a single digit, so Moolank = {day}."
    return f"Day of birth {day}: " + " → ".join(chain) + f". Moolank = {calculate_moolank(parsed)}."


def explain_bhagyank(dob):
    parsed = parse_dob(dob)
    digits = [int(d) for d in f"{parsed.day:02d}{parsed.month:02d}{parsed.year:04d}"]
    total = sum(digits)
    text = f"{'+'.join(map(str, digits))} = {total}"
    chain = _reduce_steps(total)
    if chain:
        text += " → " + " → ".join(chain)
    return text + f". Bhagyank = {calculate_bhagyank(parsed)}."
