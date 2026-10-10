"""
Screening thresholds.

IMPORTANT: These values are ILLUSTRATIVE company-policy settings for a
portfolio demo, not legal standards. Real companies set their own limits
based on counsel's advice, fair market value studies, and current CMS
Open Payments thresholds (which change every year). Update them here.
"""

# --- Meals (PhRMA Code: modest, occasional, tied to an informational presentation) ---
MEAL_LIMIT_PER_PERSON = 125.00          # example company policy cap (USD)
MAX_MEALS_PER_HCP_PER_QUARTER = 4       # "occasional" threshold for this demo

# --- Speaker / consulting fees (must reflect fair market value) ---
# Example hourly fair-market-value ranges by specialty (USD per hour).
FMV_HOURLY_RANGE = {
    "Pulmonology": (250, 450),
    "Infectious Disease": (250, 450),
    "Primary Care": (150, 300),
    "Pediatrics": (150, 300),
    "Cardiology": (300, 500),
}
DEFAULT_FMV_RANGE = (150, 400)

# --- Gifts and items (PhRMA Code) ---
# Non-educational branded items (pens, mugs, etc.) are not permitted.
# Educational items are allowed if modest; this demo uses $100 as the cap.
EDUCATIONAL_ITEM_LIMIT = 100.00

# Venue keywords that suggest entertainment or recreation (prohibited).
ENTERTAINMENT_KEYWORDS = [
    "golf", "concert", "spa", "resort", "casino", "sporting event",
    "stadium", "box seats", "theater", "ski", "yacht", "wine tasting",
]

# --- Sunshine Act / Open Payments ---
# Fields a payment record needs before it can be reported to CMS.
REQUIRED_SUNSHINE_FIELDS = ["hcp_npi", "hcp_name", "date", "amount", "nature_of_payment"]

# --- Risk scoring ---
SEVERITY_POINTS = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
