"""
AI review of free-text notes using the Claude API.

Rules catch numbers (amounts, limits). Risky intent usually hides in the
words, e.g. a payment tied to prescribing. Claude reads each note and
returns any concerns as JSON, with a plain-language explanation.

Every AI flag is a suggestion for a human compliance reviewer, never a
final decision.
"""
import json
import os

SYSTEM_PROMPT = """You are assisting a pharmaceutical healthcare compliance reviewer.
You will receive one record of an interaction between a company representative and a
healthcare professional (HCP). Review the free-text NOTES for compliance risks under:
- Anti-Kickback Statute (payments or benefits tied to prescribing, referrals, or switching patients)
- PhRMA Code on Interactions with HCPs (entertainment, recreation, lavish hospitality, non-educational gifts, spouse/guest benefits)
- False Claims Act (guidance on coding or billing to get coverage for uses that wouldn't otherwise be covered)
- Off-label promotion (promoting uses outside the approved label)

Only flag concerns supported by the text. If the note is routine, return no flags.
Respond with ONLY a JSON object, no other text, in this shape:
{"flags": [{"severity": "HIGH|MEDIUM|LOW", "regulation": "<short name>", "finding": "<one or two plain-language sentences quoting the concerning phrase>"}]}"""


def _record_text(rec):
    return (
        f"Type: {rec['nature_of_payment']}\nAmount: ${rec['amount']}\n"
        f"Specialty: {rec['specialty']}\nVenue: {rec['venue']}\nNotes: {rec['notes']}"
    )


def _parse(text):
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(text)
    return data.get("flags", [])


def review_notes(records, model=None, verbose=True):
    """Send each record's notes to Claude. Returns a list of flags."""
    import anthropic  # imported here so rule-only runs don't need the package

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    model = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
    flags = []
    for i, rec in enumerate(records, 1):
        if not rec["notes"].strip():
            continue
        if verbose:
            print(f"  AI review {i}/{len(records)}: {rec['record_id']}", end="\r")
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": _record_text(rec)}],
            )
            text = "".join(b.text for b in resp.content if b.type == "text")
            for f in _parse(text):
                flags.append({
                    "record_id": rec["record_id"],
                    "source": "ai",
                    "check": "ai_note_review",
                    "severity": f.get("severity", "MEDIUM").upper(),
                    "regulation": f.get("regulation", ""),
                    "finding": f.get("finding", ""),
                })
        except Exception as e:  # keep going if one call fails
            flags.append({
                "record_id": rec["record_id"], "source": "ai", "check": "ai_error",
                "severity": "LOW", "regulation": "",
                "finding": f"AI review failed ({type(e).__name__}); review this note manually.",
            })
    if verbose:
        print()
    return flags
