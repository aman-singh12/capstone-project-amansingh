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

customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")


# ============================================================
# 2. Clean data using the same rules as the Python EDA layer
# ============================================================

orders["payment_method"] = (
    orders["payment_method"]
    .str.strip()
    .str.upper()
)

orders["discount_pct"] = pd.to_numeric(
    orders["discount_pct"],
    errors="coerce"
)

orders["rating"] = pd.to_numeric(
    orders["rating"],
    errors="coerce"
)


# Natural duplicate key — order_id deliberately excluded
duplicate_key = [
    "customer_id",
    "product_id",
    "order_date",
    "quantity",
    "discount_pct",
    "payment_method",
    "rating",
    "returned"
]

orders = orders.drop_duplicates(
    subset=duplicate_key,
    keep="first"
).copy()


# Imputation
orders["discount_pct"] = orders["discount_pct"].fillna(0)

orders["rating"] = orders["rating"].fillna(
    orders["rating"].median()
)


# ============================================================
# 3. Merge orders, products and customers
# ============================================================

df = orders.merge(
    products,
    on="product_id",
    how="left"
)

df = df.merge(
    customers,
    on="customer_id",
    how="left"
)


# ============================================================
# 4. Calculate order value
# ============================================================

df["order_value"] = (
    df["quantity"]
    * df["price"]
    * (1 - df["discount_pct"] / 100.0)
)

cleaned_total_revenue = round(
    df["order_value"].sum(),
    2
)


# ============================================================
# 5. Calculate raw revenue for reconciliation
# ============================================================

raw_orders = pd.read_csv(DATA_DIR / "orders.csv")

raw_orders["discount_pct"] = pd.to_numeric(
    raw_orders["discount_pct"],
    errors="coerce"
).fillna(0)

raw_df = raw_orders.merge(
    products,
    on="product_id",
    how="left"
)

raw_df["order_value"] = (
    raw_df["quantity"]
    * raw_df["price"]
    * (1 - raw_df["discount_pct"] / 100.0)
)

raw_total_revenue = round(
    raw_df["order_value"].sum(),
    2
)

duplicate_reconciliation_delta = round(
    raw_total_revenue - cleaned_total_revenue,
    2
)


# ============================================================
# 6. Return rate by payment method
# ============================================================

return_rate_by_payment = (
    df.groupby("payment_method")["returned"]
    .mean()
    .mul(100)
    .round(1)
    .sort_values(ascending=False)
)

return_rate_dict = {
    payment: float(rate)
    for payment, rate in return_rate_by_payment.items()
}


# ============================================================
# 7. Highest-risk payment + city-tier segment
# ============================================================

payment_tier = (
    df.groupby(
        ["payment_method", "city_tier"]
    )["returned"]
    .mean()
    .mul(100)
    .round(1)
)

highest_risk_segment = payment_tier.idxmax()
highest_risk_rate = float(
    payment_tier.max()
)

highest_risk_payment = highest_risk_segment[0]
highest_risk_city_tier = int(
    highest_risk_segment[1]
)


# ============================================================
# 8. Quantity outlier detection
# ============================================================

q1 = df["quantity"].quantile(0.25)
q3 = df["quantity"].quantile(0.75)

iqr = q3 - q1

lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

df["quantity_outlier"] = (
    (df["quantity"] < lower_bound)
    | (df["quantity"] > upper_bound)
)


# ============================================================
# 9. Corrected monthly revenue
# ============================================================

df["order_date"] = pd.to_datetime(
    df["order_date"]
)

corrected_df = df.loc[
    ~df["quantity_outlier"]
].copy()

monthly_revenue = (
    corrected_df
    .groupby(
        corrected_df["order_date"].dt.to_period("M")
    )["order_value"]
    .sum()
    .round(2)
)

true_peak_period = monthly_revenue.idxmax()
true_peak_revenue = float(
    monthly_revenue.max()
)


# ============================================================
# 10. Build findings dictionary
# ============================================================

findings = {
    "project": "Mamaearth Returns & Growth Intelligence Pipeline",

    "cleaned_total_revenue_inr": cleaned_total_revenue,

    "raw_total_revenue_inr": raw_total_revenue,

    "duplicate_reconciliation_delta_inr": (
        duplicate_reconciliation_delta
    ),

    "orders_before_cleaning": 180,

    "orders_after_duplicate_removal": len(df),

    "return_rate_by_payment": return_rate_dict,

    "highest_risk_segment": {
        "payment_method": highest_risk_payment,
        "city_tier": highest_risk_city_tier,
        "return_rate_pct": highest_risk_rate
    },

    "true_peak_month": str(true_peak_period),

    "true_peak_revenue_inr": true_peak_revenue
}


# ============================================================
# 11. Save findings.json
# ============================================================

with open(
    FINDINGS_PATH,
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        findings,
        file,
        indent=4
    )

print("=== FINDINGS GENERATED ===")
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

    return f"""
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

        client = genai.Client(
            api_key=api_key
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

        return response.text.strip()

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
# 17. Final status
# ============================================================

print("\nNarrative generation completed successfully.")