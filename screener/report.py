"""
Combine rule and AI flags into a risk-ranked report.
"""
import csv
from collections import defaultdict
from datetime import datetime

from . import config

RISK_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "CLEAR": 3}


def score_records(records, flags):
    """Return one summary row per record, sorted from highest to lowest risk."""
    by_record = defaultdict(list)
    for f in flags:
        by_record[f["record_id"]].append(f)

    rows = []
    for rec in records:
        fl = by_record.get(rec["record_id"], [])
        score = sum(config.SEVERITY_POINTS.get(f["severity"], 1) for f in fl)
        if any(f["severity"] == "HIGH" for f in fl) or score >= 4:
            risk = "HIGH"
        elif score >= 2:
            risk = "MEDIUM"
        elif score > 0:
            risk = "LOW"
        else:
            risk = "CLEAR"
        rows.append({
            "record_id": rec["record_id"],
            "risk": risk,
            "score": score,
            "hcp_name": rec["hcp_name"],
            "nature_of_payment": rec["nature_of_payment"],
            "amount": rec["amount"],
            "date": rec["date"],
            "rep_name": rec["rep_name"],
            "num_flags": len(fl),
            "sources": "+".join(sorted({f["source"] for f in fl})),
        })
    rows.sort(key=lambda r: (RISK_ORDER[r["risk"]], -r["score"]))
    return rows


def write_csv(path, rows):
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_markdown(path, summary, flags, records, used_ai):
    by_record = defaultdict(list)
    for f in flags:
        by_record[f["record_id"]].append(f)
    rec_lookup = {r["record_id"]: r for r in records}
    counts = defaultdict(int)
    for r in summary:
        counts[r["risk"]] += 1

    lines = [
        "# HCP Interaction Compliance Screening Report",
        "",
        f"Generated {datetime.now():%Y-%m-%d %H:%M} · {len(records)} records screened · "
        f"AI note review: {'on' if used_ai else 'off'}",
        "",
        "**All data is synthetic. Every flag is a lead for human compliance review, not a finding of a violation.**",
        "",
        "| Risk | Records |",
        "| --- | --- |",
    ]
    for level in ("HIGH", "MEDIUM", "LOW", "CLEAR"):
        lines.append(f"| {level} | {counts[level]} |")
    lines += ["", "## Flagged records", ""]

    for r in summary:
        if r["risk"] == "CLEAR":
            continue
        rec = rec_lookup[r["record_id"]]
        lines.append(f"### {r['record_id']} · {r['risk']} · {rec['hcp_name']} · "
                     f"{rec['nature_of_payment']} ${float(rec['amount']):,.2f}")
        lines.append(f"*{rec['date']} · {rec['venue'] or 'no venue'} · rep {rec['rep_name']}*")
        lines.append("")
        lines.append(f"> {rec['notes']}")
        lines.append("")
        for f in by_record[r["record_id"]]:
            tag = "AI" if f["source"] == "ai" else "Rule"
            lines.append(f"- **{f['severity']}** [{tag}] {f['regulation']}: {f['finding']}")
        lines.append("")
    path.write_text("\n".join(lines))
