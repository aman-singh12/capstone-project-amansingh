import json
import os
import re
from pathlib import Path

import pandas as pd

# ============================================================
# Mamaearth Returns & Growth Intelligence Pipeline
# GenAI Narrator Layer
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
NARRATOR_DIR = BASE_DIR / "narrator"

FINDINGS_PATH = NARRATOR_DIR / "findings.json"


# ============================================================
# 1. Load raw data
# ============================================================


with open(
    FINDINGS_PATH,
    "r",
    encoding="utf-8"
) as file:
    findings = json.load(file)

print("=== FINDINGS LOADED ===")
print(json.dumps(findings, indent=4))

# ============================================================
# 12. Offline fallback narrative
# ============================================================

def generate_scr_narrative_offline(findings):
    """
    Generates a deterministic Situation-Complication-Resolution
    narrative when Gemini API is unavailable.
    """

    cod_rate = findings[
        "return_rate_by_payment"
    ]["COD"]

    highest_risk = findings[
        "highest_risk_segment"
    ]

    narrative = f"""
SITUATION

The cleaned Mamaearth order dataset contains
{findings["orders_after_duplicate_removal"]} valid orders.
After removing duplicate records and applying the defined
missing-value treatment, cleaned revenue is
₹{findings["cleaned_total_revenue_inr"]:,.2f}.

COMPLICATION

The raw dataset reports revenue of
₹{findings["raw_total_revenue_inr"]:,.2f}.
The difference of
₹{findings["duplicate_reconciliation_delta_inr"]:,.2f}
is explained by duplicate orders in the raw dataset.

Returns are concentrated around COD transactions.
COD has a return rate of {cod_rate:.1f}%.
The highest-risk segment is COD combined with city tier
{highest_risk["city_tier"]}, where the return rate is
{highest_risk["return_rate_pct"]:.1f}%.

RESOLUTION

Operations should prioritize COD return reduction,
especially in city tier {highest_risk["city_tier"]}.
The corrected revenue analysis shows that
{findings["true_peak_month"]} is the true revenue peak,
with revenue of ₹{findings["true_peak_revenue_inr"]:,.2f},
after excluding the identified quantity outliers.

The key business takeaway is that revenue reporting should
use the cleaned dataset, while return-risk interventions
should focus first on high-risk COD segments.
""".strip()

    return {
        "status": "success",
        "narrative": narrative,
        "tokens": None
    }


# ============================================================
# 13. Gemini narrative generation
# ============================================================

def generate_scr_narrative(findings):
    """
    Generate an executive Situation-Complication-Resolution
    narrative using Gemini.

    If no API key is available or the API call fails,
    use the deterministic offline fallback.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("\nGemini API key not found.")
        print("Using offline fallback narrative.")
        return generate_scr_narrative_offline(findings)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=15000)
        )

        system_instruction = """
You are a Senior Data Analyst presenting findings to
Mamaearth regional operations leaders and finance heads.

Write a concise executive narrative using exactly this structure:

SITUATION
COMPLICATION
RESOLUTION

Use only the supplied findings.

Do not invent numbers.
Do not change numbers.
Do not introduce unsupported causes.
Focus on revenue quality, returns, and operational action.

The narrative should be professional, concise and
business-oriented.
"""

        user_prompt = f"""
Analyze the following verified findings:

{json.dumps(findings, indent=4)}

Create an executive Situation-Complication-Resolution
narrative for regional operations and finance leadership.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config={
                "system_instruction": system_instruction,
                "temperature": 0.0,
                "max_output_tokens": 500
            }
        )

        return {
            "status": "success",
            "narrative": response.text.strip(),
            "tokens": getattr(response.usage_metadata, "total_token_count", None)
        }

    except Exception as error:
        print("\nGemini generation failed.")
        print("Reason:", error)
        print("Using offline fallback narrative.")

        return generate_scr_narrative_offline(
            findings
        )


# ============================================================
# 14. Numeric accuracy validation
# ============================================================

def normalize_number(number):
    """
    Convert a numeric value into a format suitable for
    checking inside generated text.
    """

    return f"{number:,.2f}"


def validate_numeric_accuracy(
    narrative,
    findings
):
    """
    Check whether the generated narrative preserves
    the key verified numbers.
    """
    if isinstance(narrative, dict):
        narrative = narrative["narrative"]

    required_numbers = [
        normalize_number(
            findings["cleaned_total_revenue_inr"]
        ),
        f'{findings["return_rate_by_payment"]["COD"]:.1f}',
        f'{findings["highest_risk_segment"]["return_rate_pct"]:.1f}',
        normalize_number(
            findings["duplicate_reconciliation_delta_inr"]
        ),
        normalize_number(
            findings["true_peak_revenue_inr"]
        )
    ]

    normalized_text = narrative.replace(
        ",",
        ""
    )

    missing_numbers = []

    for number in required_numbers:
        if number.replace(",", "") not in normalized_text:
            missing_numbers.append(number)

    if missing_numbers:
        print("\nWARNING: Some required numbers were not found:")
        print(missing_numbers)
        return False

    print("\nNumeric accuracy check: PASSED")
    return True


# ============================================================
# 15. Generate narrative
# ============================================================

narrative = generate_scr_narrative(
    findings
)

print("\n=== GENERATED NARRATIVE ===")
print(narrative)


# ============================================================
# 16. Validate generated narrative
# ============================================================

validate_numeric_accuracy(
    narrative,
    findings
)

# ============================================================
# 17. Save sample narrative output
# ============================================================

sample_output_path = NARRATOR_DIR / "sample_output.txt"

with open(
    sample_output_path,
    "w",
    encoding="utf-8"
) as file:
    if isinstance(narrative, dict):
        file.write(narrative["narrative"])
    else:
        file.write(narrative)

print(
    f"\nSample output saved to: {sample_output_path}"
)

# ============================================================
# 18. Final status
# ============================================================

print("\nNarrative generation completed successfully.")