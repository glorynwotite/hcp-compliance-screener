# HCP Interaction Compliance Screener

An AI-assisted tool that screens records of interactions between pharmaceutical company representatives and healthcare professionals (HCPs) for compliance risk. It combines rule-based checks for clear limits with Claude API review of free-text notes, then produces a risk-ranked report for a human compliance reviewer.

**All data in this project is synthetic.** Every flag is a lead for human review, not a determination that a violation occurred.

## Why this exists

Compliance teams monitor thousands of HCP interactions: meals, speaker fees, consulting payments, travel, and educational items. Numeric limits are easy to check with rules. The harder risks are written in plain language, such as a consulting arrangement described as continuing "as long as his new-start numbers stay strong." This tool pairs both approaches so reviewers can focus on the records that matter.

## What it checks

| Check | Method | Regulation or standard |
| --- | --- | --- |
| Meal cost per attendee over policy limit | Rule | PhRMA Code (modest meals) |
| Too many meals for one HCP in a quarter | Rule | PhRMA Code (occasional meals) |
| Entertainment or recreational venues | Rule | PhRMA Code; Anti-Kickback Statute |
| Speaker or consulting fees above fair market value | Rule | Anti-Kickback Statute |
| Non-educational gifts; educational items over limit | Rule | PhRMA Code |
| Missing fields needed for CMS reporting | Rule | Physician Payments Sunshine Act (Open Payments) |
| Payments tied to prescribing or switching patients | AI | Anti-Kickback Statute |
| Billing or coding guidance to obtain coverage | AI | False Claims Act |
| Off-label promotion | AI | FDA promotional rules |
| Spouse or guest benefits, lavish hospitality | AI | PhRMA Code |

Thresholds in `screener/config.py` are illustrative company-policy settings, not legal standards. Real programs set limits with counsel, fair market value studies, and current CMS Open Payments thresholds.

## How it works

```
data/hcp_interactions.csv
        │
        ├── screener/rules.py      → rule flags (amounts, venues, frequency, missing fields)
        ├── screener/llm_review.py → AI flags (Claude reads each note, returns JSON)
        │
        └── screener/report.py     → risk score per record → HIGH / MEDIUM / LOW / CLEAR
                                     output/report.md, record_risk_summary.csv, all_flags.csv
```

Each flag records its source (rule or AI), severity, the regulation involved, and a plain-language finding, so a reviewer can see exactly why a record was raised.

## Run it

Works locally or in GitHub Codespaces (click **Code → Codespaces → Create codespace**).

```bash
pip install -r requirements.txt
python data/generate_data.py      # create 50 synthetic records
python main.py --no-ai            # rules only, no API key needed
```

To add the AI review, get an API key at https://console.anthropic.com, then:

```bash
cp .env.example .env              # paste your key into .env
python main.py
```

Run the tests with `pytest`.

## Results

The synthetic dataset includes 10 planted issues plus a group of over-frequent meals.

- **Rules only:** caught 7 of 10 planted issues. The 3 it missed are text-only risks (payment tied to prescribing, a quid pro quo request, and off-label/billing guidance), which have no numeric signal.
- **Rules + AI:** caught all 10 planted issues with no false alarms on the 40 routine records. The AI flagged all 3 text-only risks the rules missed and added context the rules couldn't see, such as spouse travel on a resort trip and a dinner with no presentation. It did not flag the over-FMV fee or the missing NPI, which have no signal in the note text; the rules caught both. This is why the tool uses both methods.

## Responsible AI design

- **Human in the loop.** The tool ranks and explains; a compliance reviewer decides.
- **Explainable flags.** Every AI flag must quote the concerning phrase and name the regulation.
- **Failure is visible.** If an AI call fails, the record is flagged for manual review instead of silently passing.
- **No real data.** Synthetic records only; real HCP or patient data would require privacy review before use.
- **Known limits.** Keyword rules can miss euphemisms and over-flag innocent text; the AI can produce false positives or miss subtle risk. Neither replaces an effective compliance program (OIG's seven elements) or legal judgment.
