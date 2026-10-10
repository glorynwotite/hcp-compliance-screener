"""
Generate SYNTHETIC HCP interaction records for testing the screener.

All names, NPIs, and events are fake. Most records are clean; a set of
"planted" records contain known issues so we can check the screener
catches them.

Run:  python data/generate_data.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)  # same data every run

OUT = Path(__file__).parent / "hcp_interactions.csv"

FIELDS = [
    "record_id", "hcp_npi", "hcp_name", "specialty", "date", "nature_of_payment",
    "amount", "attendees", "hours", "venue", "rep_name", "notes",
]

HCPS = [
    ("1003000001", "Dr. Alicia Moreno", "Pulmonology"),
    ("1003000002", "Dr. Ben Okafor", "Infectious Disease"),
    ("1003000003", "Dr. Carla Nguyen", "Primary Care"),
    ("1003000004", "Dr. David Levin", "Cardiology"),
    ("1003000005", "Dr. Erin Shah", "Pediatrics"),
    ("1003000006", "Dr. Frank Ito", "Pulmonology"),
    ("1003000007", "Dr. Grace Adeyemi", "Primary Care"),
    ("1003000008", "Dr. Hector Ruiz", "Infectious Disease"),
]
REPS = ["J. Carter", "M. Patel", "S. Kim", "T. Brooks"]

CLEAN_MEAL_NOTES = [
    "Lunch during in-office presentation on approved product label.",
    "Working lunch with clinic staff; reviewed patient support program materials.",
    "Breakfast with care team during disease-state education session.",
    "Lunch provided with presentation of new safety information.",
]
CLEAN_FEE_NOTES = [
    "Speaker program on approved indication; slides approved by medical/legal review.",
    "Advisory board participation under signed contract; deliverables received.",
    "Consulting on trial design under written agreement with documented need.",
]


def rand_date(start=date(2026, 7, 1), days=90):
    return (start + timedelta(days=random.randint(0, days))).isoformat()


def clean_record(i):
    npi, name, spec = random.choice(HCPS)
    kind = random.choice(["Meal", "Meal", "Meal", "Speaker Fee", "Consulting Fee", "Educational Item"])
    rec = dict(record_id=f"R{i:03d}", hcp_npi=npi, hcp_name=name, specialty=spec,
               date=rand_date(), nature_of_payment=kind, attendees="", hours="",
               venue="", rep_name=random.choice(REPS), notes="")
    if kind == "Meal":
        attendees = random.randint(2, 8)
        rec.update(amount=round(attendees * random.uniform(18, 45), 2), attendees=attendees,
                   venue=random.choice(["Clinic office", "Hospital conference room", "Medical office"]),
                   notes=random.choice(CLEAN_MEAL_NOTES))
    elif kind in ("Speaker Fee", "Consulting Fee"):
        hours = random.choice([2, 3, 4])
        rec.update(amount=hours * 300, hours=hours, venue="Hotel meeting room",
                   notes=random.choice(CLEAN_FEE_NOTES))
    else:
        rec.update(amount=round(random.uniform(20, 80), 2), venue="Clinic office",
                   notes="Anatomical model for patient education.")
    return rec


# Records with known problems. "expected" documents what SHOULD be flagged.
PLANTED = [
    dict(hcp_npi="1003000001", hcp_name="Dr. Alicia Moreno", specialty="Pulmonology",
         nature_of_payment="Meal", amount=980.00, attendees=2, venue="Steakhouse downtown",
         notes="Dinner after clinic; no presentation given.", expected="Meal over limit; no educational purpose"),
    dict(hcp_npi="1003000004", hcp_name="Dr. David Levin", specialty="Cardiology",
         nature_of_payment="Meal", amount=210.00, attendees=2, venue="Country club golf outing",
         notes="Round of golf followed by lunch.", expected="Entertainment venue"),
    dict(hcp_npi="1003000002", hcp_name="Dr. Ben Okafor", specialty="Infectious Disease",
         nature_of_payment="Speaker Fee", amount=6000.00, hours=2, venue="Hotel meeting room",
         notes="Speaker program.", expected="Fee far above FMV"),
    dict(hcp_npi="1003000003", hcp_name="Dr. Carla Nguyen", specialty="Primary Care",
         nature_of_payment="Gift", amount=45.00, venue="Clinic office",
         notes="Branded coffee mugs and pens for the office.", expected="Non-educational gift"),
    dict(hcp_npi="1003000005", hcp_name="Dr. Erin Shah", specialty="Pediatrics",
         nature_of_payment="Educational Item", amount=350.00, venue="Clinic office",
         notes="Tablet for reviewing patient education videos.", expected="Educational item over limit"),
    dict(hcp_npi="1003000006", hcp_name="Dr. Frank Ito", specialty="Pulmonology",
         nature_of_payment="Consulting Fee", amount=1200.00, hours=3, venue="Hotel meeting room",
         notes="Told him we'd keep the consulting work coming as long as his new-start numbers stay strong.",
         expected="Payment tied to prescribing (AKS risk) - text only"),
    dict(hcp_npi="1003000007", hcp_name="Dr. Grace Adeyemi", specialty="Primary Care",
         nature_of_payment="Meal", amount=96.00, attendees=4, venue="Clinic office",
         notes="Lunch. She mentioned she'd switch her patients over if we sponsor her daughter's school fundraiser.",
         expected="Quid pro quo language - text only"),
    dict(hcp_npi="", hcp_name="Dr. Hector Ruiz", specialty="Infectious Disease",
         nature_of_payment="Speaker Fee", amount=900.00, hours=3, venue="Hotel meeting room",
         notes="Speaker program on approved indication.", expected="Missing NPI (Sunshine)"),
    dict(hcp_npi="1003000008", hcp_name="Dr. Hector Ruiz", specialty="Infectious Disease",
         nature_of_payment="Consulting Fee", amount=1500.00, hours=5, venue="Hotel meeting room",
         notes="Discussed off-label use in pediatric patients and how to code it so insurance covers it.",
         expected="Off-label promotion / billing guidance - text only"),
    dict(hcp_npi="1003000004", hcp_name="Dr. David Levin", specialty="Cardiology",
         nature_of_payment="Travel", amount=2400.00, venue="Beach resort",
         notes="Covered flights and resort stay for him and his spouse for the advisory meeting.",
         expected="Resort venue; spouse travel"),
]

# Frequency issue: 6 meals for one HCP in one quarter.
FREQUENT = [
    dict(hcp_npi="1003000003", hcp_name="Dr. Carla Nguyen", specialty="Primary Care",
         nature_of_payment="Meal", amount=60.00 + k, attendees=3, venue="Clinic office",
         notes="Lunch during in-office presentation on approved product label.",
         expected="Meal frequency" if k == 0 else "")
    for k in range(6)
]


def main():
    rows = [clean_record(i) for i in range(1, 35)]
    n = len(rows)
    for extra in PLANTED + FREQUENT:
        n += 1
        rec = dict(record_id=f"R{n:03d}", date=rand_date(), attendees="", hours="",
                   rep_name=random.choice(REPS))
        rec.update({k: v for k, v in extra.items() if k != "expected"})
        rows.append(rec)
    random.shuffle(rows)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} synthetic records to {OUT}")


if __name__ == "__main__":
    main()
