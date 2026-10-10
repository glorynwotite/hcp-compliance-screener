"""
HCP Interaction Compliance Screener

Usage:
    python main.py              # rules + Claude AI note review
    python main.py --no-ai      # rules only (no API key needed)
    python main.py --input path/to/records.csv
"""
import argparse
import csv
import os
from pathlib import Path

from screener.rules import run_rules
from screener.report import score_records, write_csv, write_markdown

ROOT = Path(__file__).parent


def load_records(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser(description="Screen HCP interactions for compliance risk.")
    parser.add_argument("--input", default=ROOT / "data" / "hcp_interactions.csv")
    parser.add_argument("--output", default=ROOT / "output")
    parser.add_argument("--no-ai", action="store_true", help="skip the Claude note review")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    records = load_records(args.input)
    print(f"Loaded {len(records)} records from {args.input}")

    flags = run_rules(records)
    print(f"Rule checks: {len(flags)} flags")

    used_ai = False
    if not args.no_ai:
        if os.getenv("ANTHROPIC_API_KEY"):
            from screener.llm_review import review_notes
            ai_flags = review_notes(records)
            print(f"AI note review: {len(ai_flags)} flags")
            flags += ai_flags
            used_ai = True
        else:
            print("No ANTHROPIC_API_KEY found; skipping AI review (see README).")

    out = Path(args.output)
    out.mkdir(exist_ok=True)
    summary = score_records(records, flags)
    write_csv(out / "record_risk_summary.csv", summary)
    write_csv(out / "all_flags.csv", flags)
    write_markdown(out / "report.md", summary, flags, records, used_ai)

    for level in ("HIGH", "MEDIUM", "LOW"):
        n = sum(r["risk"] == level for r in summary)
        print(f"  {level}: {n}")
    print(f"Reports written to {out}/")


if __name__ == "__main__":
    main()
