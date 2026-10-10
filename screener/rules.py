"""
Rule-based compliance checks.

Each check looks at one record (or the whole dataset, for frequency) and
returns a list of flags. A flag is a dict with:
    record_id, source, check, severity, regulation, finding
"""
from collections import defaultdict
from datetime import date

from . import config


def _flag(rec, check, severity, regulation, finding):
    return {
        "record_id": rec["record_id"],
        "source": "rule",
        "check": check,
        "severity": severity,
        "regulation": regulation,
        "finding": finding,
    }


def _num(value):
    """Convert a CSV cell to float; blank or bad values become None."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def check_meal_limit(rec):
    if rec["nature_of_payment"] != "Meal":
        return []
    amount, attendees = _num(rec["amount"]), _num(rec["attendees"]) or 1
    per_person = amount / attendees
    if per_person > config.MEAL_LIMIT_PER_PERSON:
        return [_flag(rec, "meal_limit", "MEDIUM", "PhRMA Code (modest meals)",
                      f"${per_person:,.2f} per person exceeds ${config.MEAL_LIMIT_PER_PERSON:,.2f} limit.")]
    return []


def check_entertainment(rec):
    text = f"{rec['venue']} {rec['notes']}".lower()
    hits = [k for k in config.ENTERTAINMENT_KEYWORDS if k in text]
    if hits:
        return [_flag(rec, "entertainment", "HIGH", "PhRMA Code (no entertainment/recreation); AKS",
                      f"Possible entertainment or recreation: {', '.join(hits)}.")]
    return []


def check_fair_market_value(rec):
    if rec["nature_of_payment"] not in ("Speaker Fee", "Consulting Fee"):
        return []
    amount, hours = _num(rec["amount"]), _num(rec["hours"])
    if not hours:
        return [_flag(rec, "fmv_missing_hours", "MEDIUM", "AKS (fair market value)",
                      "Fee recorded without hours, so fair market value can't be checked.")]
    low, high = config.FMV_HOURLY_RANGE.get(rec["specialty"], config.DEFAULT_FMV_RANGE)
    rate = amount / hours
    if rate > high:
        sev = "HIGH" if rate > 2 * high else "MEDIUM"
        return [_flag(rec, "fmv_above_range", sev, "AKS (fair market value)",
                      f"${rate:,.0f}/hr is above the ${low}-${high}/hr range for {rec['specialty']}.")]
    return []


def check_gifts(rec):
    kind, amount = rec["nature_of_payment"], _num(rec["amount"])
    if kind == "Gift":
        return [_flag(rec, "non_educational_gift", "MEDIUM", "PhRMA Code (no non-educational items)",
                      "Non-educational gifts are not permitted, regardless of value.")]
    if kind == "Educational Item" and amount > config.EDUCATIONAL_ITEM_LIMIT:
        return [_flag(rec, "educational_item_limit", "LOW", "PhRMA Code (modest educational items)",
                      f"${amount:,.2f} exceeds the ${config.EDUCATIONAL_ITEM_LIMIT:,.2f} educational item limit.")]
    return []


def check_sunshine_fields(rec):
    missing = [f for f in config.REQUIRED_SUNSHINE_FIELDS if not str(rec.get(f, "")).strip()]
    if missing:
        return [_flag(rec, "sunshine_missing_fields", "MEDIUM", "Physician Payments Sunshine Act (Open Payments)",
                      f"Missing fields needed for CMS reporting: {', '.join(missing)}.")]
    return []


RECORD_CHECKS = [check_meal_limit, check_entertainment, check_fair_market_value,
                 check_gifts, check_sunshine_fields]


def check_meal_frequency(records):
    """Flag HCPs who received too many meals in one calendar quarter."""
    counts = defaultdict(list)
    for rec in records:
        if rec["nature_of_payment"] == "Meal":
            d = date.fromisoformat(rec["date"])
            quarter = f"{d.year}-Q{(d.month - 1) // 3 + 1}"
            counts[(rec["hcp_name"], quarter)].append(rec)
    flags = []
    for (hcp, quarter), recs in counts.items():
        if len(recs) > config.MAX_MEALS_PER_HCP_PER_QUARTER:
            for rec in recs:
                flags.append(_flag(rec, "meal_frequency", "LOW", "PhRMA Code (occasional meals)",
                                   f"{hcp} received {len(recs)} meals in {quarter} "
                                   f"(limit {config.MAX_MEALS_PER_HCP_PER_QUARTER})."))
    return flags


def run_rules(records):
    flags = []
    for rec in records:
        for check in RECORD_CHECKS:
            flags.extend(check(rec))
    flags.extend(check_meal_frequency(records))
    return flags
