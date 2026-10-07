import json
from pathlib import Path

import pandas as pd

# ============================================================
# Mamaearth Returns & Growth Intelligence Pipeline
# Python Cleaning + EDA Layer
# ============================================================

# ------------------------------------------------------------
# 1. Load raw CSV files
# ------------------------------------------------------------

customers = pd.read_csv("data/customers.csv")
products = pd.read_csv("data/products.csv")
orders = pd.read_csv("data/orders.csv")

print("=== RAW DATA SHAPES ===")
print("Customers:", customers.shape)
print("Products :", products.shape)
print("Orders   :", orders.shape)


# ------------------------------------------------------------
# 2. Verify raw orders dataset
# ------------------------------------------------------------

print("\n=== RAW ORDERS CHECK ===")
print("Expected orders shape: (180, 9)")
print("Actual orders shape  :", orders.shape)


# ------------------------------------------------------------
# 3. Clean payment method
# ------------------------------------------------------------

orders["payment_method"] = (
    orders["payment_method"]
    .str.strip()
    .str.upper()
)

print("\n=== PAYMENT METHOD COUNTS ===")
print(orders["payment_method"].value_counts().sort_index())


# ------------------------------------------------------------
# 4. Check missing values BEFORE duplicate removal
# ------------------------------------------------------------

print("\n=== MISSING VALUES BEFORE CLEANING ===")
print(orders[["discount_pct", "rating"]].isna().sum())


# ------------------------------------------------------------
# 5. Detect duplicate orders
# Natural duplicate key excludes order_id
# ------------------------------------------------------------

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

duplicate_mask = orders.duplicated(
    subset=duplicate_key,
    keep="first"
)

print("\n=== DUPLICATE CHECK ===")
print("Duplicate rows found:", duplicate_mask.sum())

if duplicate_mask.sum() > 0:
    print("Duplicate order IDs:")
    print(orders.loc[duplicate_mask, "order_id"].tolist())


# ------------------------------------------------------------
# 6. Remove duplicates
# ------------------------------------------------------------

orders = orders.loc[~duplicate_mask].copy()

print("\n=== AFTER DUPLICATE REMOVAL ===")
print("Orders remaining:", len(orders))


# ------------------------------------------------------------
# 7. Impute missing values
# ------------------------------------------------------------

orders["discount_pct"] = orders["discount_pct"].fillna(0)

rating_median = orders["rating"].median()
orders["rating"] = orders["rating"].fillna(rating_median)

print("\n=== IMPUTATION ===")
print("Rating median used:", rating_median)
print("Missing discount_pct:", orders["discount_pct"].isna().sum())
print("Missing rating      :", orders["rating"].isna().sum())


# ------------------------------------------------------------
# 8. Merge orders with products and customers
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# 9. Calculate cleaned order revenue
# ------------------------------------------------------------

df["order_value"] = (
    df["quantity"]
    * df["price"]
    * (1 - df["discount_pct"] / 100.0)
)

cleaned_revenue = df["order_value"].sum()

print("\n=== CLEANED REVENUE ===")
print(f"Cleaned revenue: ₹{cleaned_revenue:,.2f}")


# ------------------------------------------------------------
# 10. Raw revenue reconciliation
# ------------------------------------------------------------

raw_orders = pd.read_csv("data/orders.csv")

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

raw_revenue = raw_df["order_value"].sum()

revenue_difference = raw_revenue - cleaned_revenue

print("\n=== REVENUE RECONCILIATION ===")
print(f"Raw revenue    : ₹{raw_revenue:,.2f}")
print(f"Cleaned revenue: ₹{cleaned_revenue:,.2f}")
print(f"Difference     : ₹{revenue_difference:,.2f}")


# ------------------------------------------------------------
# 11. Quantity IQR and outlier detection
# ------------------------------------------------------------

q1 = df["quantity"].quantile(0.25)
q3 = df["quantity"].quantile(0.75)

iqr = q3 - q1

lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

df["quantity_outlier"] = (
    (df["quantity"] < lower_bound)
    | (df["quantity"] > upper_bound)
)

outliers = df[df["quantity_outlier"]]

print("\n=== QUANTITY OUTLIERS ===")
print(f"Q1         : {q1}")
print(f"Q3         : {q3}")
print(f"IQR        : {iqr}")
print(f"Lower bound: {lower_bound}")
print(f"Upper bound: {upper_bound}")

print("\nOutlier orders:")
print(
    outliers[
        ["order_id", "quantity", "order_value"]
    ].to_string(index=False)
)


# ------------------------------------------------------------
# 12. Return rate by payment method
# ------------------------------------------------------------

return_rate_by_payment = (
    df.groupby("payment_method")["returned"]
    .mean()
    .mul(100)
    .round(1)
    .sort_values(ascending=False)
)

print("\n=== RETURN RATE BY PAYMENT METHOD ===")
print(return_rate_by_payment)


# ------------------------------------------------------------
# 13. Payment method × city tier
# ------------------------------------------------------------

payment_tier = (
    df.groupby(["payment_method", "city_tier"])["returned"]
    .mean()
    .mul(100)
    .round(1)
    .sort_values(ascending=False)
)

print("\n=== PAYMENT × CITY TIER RETURN RATE ===")
print(payment_tier)


# ------------------------------------------------------------
# 14. Correlation analysis
# ------------------------------------------------------------

correlation_columns = [
    "rating",
    "returned",
    "discount_pct",
    "quantity"
]

correlations = df[correlation_columns].corr()

print("\n=== CORRELATION MATRIX ===")
print(correlations.round(3))


# ------------------------------------------------------------
# 15. Monthly revenue
# ------------------------------------------------------------

df["order_date"] = pd.to_datetime(df["order_date"])

monthly_revenue = (
    df.groupby(df["order_date"].dt.to_period("M"))["order_value"]
    .sum()
    .round(2)
)

print("\n=== MONTHLY REVENUE ===")
print(monthly_revenue)


# ------------------------------------------------------------
# 16. Corrected monthly revenue excluding quantity outliers
# ------------------------------------------------------------

cleaned_without_outliers = df.loc[
    ~df["quantity_outlier"]
]

corrected_monthly_revenue = (
    cleaned_without_outliers
    .groupby(
        cleaned_without_outliers["order_date"].dt.to_period("M")
    )["order_value"]
    .sum()
    .round(2)
)

print("\n=== CORRECTED MONTHLY REVENUE ===")
print(corrected_monthly_revenue)


# ------------------------------------------------------------
# 17. Final summary
# ------------------------------------------------------------

print("\n=== FINAL SUMMARY ===")
print("Raw orders       :", len(raw_orders))
print("Cleaned orders   :", len(df))
print(f"Raw revenue      : ₹{raw_revenue:,.2f}")
print(f"Cleaned revenue  : ₹{cleaned_revenue:,.2f}")
print(f"Revenue difference: ₹{revenue_difference:,.2f}")
# ------------------------------------------------------------
# 18. Generate verified findings.json for GenAI layer
# ------------------------------------------------------------

# Highest-risk payment + city-tier segment
highest_risk_segment = payment_tier.idxmax()
highest_risk_rate = float(payment_tier.max())

highest_risk_payment = highest_risk_segment[0]
highest_risk_city_tier = int(highest_risk_segment[1])


# Convert payment return rates to a JSON-friendly dictionary
return_rate_dict = {
    payment: float(rate)
    for payment, rate in return_rate_by_payment.items()
}


# Identify the month most inflated by quantity outliers
outlier_impact = (
    monthly_revenue
    .subtract(corrected_monthly_revenue, fill_value=0)
    .round(2)
)

outlier_inflated_month = outlier_impact.idxmax()

apparent_revenue = float(
    monthly_revenue.loc[outlier_inflated_month]
)

corrected_revenue = float(
    corrected_monthly_revenue.loc[outlier_inflated_month]
)


# Identify the true revenue peak after outlier correction
true_peak_month = corrected_monthly_revenue.idxmax()

true_peak_revenue = float(
    corrected_monthly_revenue.loc[true_peak_month]
)


# Build the verified findings dictionary
findings = {
    "project": "Mamaearth Returns & Growth Intelligence Pipeline",

    "cleaned_total_revenue_inr": round(
        float(cleaned_revenue),
        2
    ),

    "raw_total_revenue_inr": round(
        float(raw_revenue),
        2
    ),

    "duplicate_reconciliation_delta_inr": round(
        float(revenue_difference),
        2
    ),

    "orders_before_cleaning": int(
        len(raw_orders)
    ),

    "orders_after_duplicate_removal": int(
        len(df)
    ),

    "return_rate_by_payment": return_rate_dict,

    "highest_risk_segment": {
        "payment_method": highest_risk_payment,
        "city_tier": highest_risk_city_tier,
        "return_rate_pct": highest_risk_rate
    },

    "true_peak_month": str(
        true_peak_month
    ),

    "true_peak_revenue_inr": round(
        true_peak_revenue,
        2
    ),

    "outlier_inflated_month": {
        "month": str(
            outlier_inflated_month
        ),
        "apparent_revenue_inr": round(
            apparent_revenue,
            2
        ),
        "corrected_revenue_inr": round(
            corrected_revenue,
            2
        )
    }
}


# Save findings.json inside the narrator folder
BASE_DIR = Path(__file__).resolve().parent.parent
FINDINGS_PATH = BASE_DIR / "narrator" / "findings.json"

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


print("\n=== FINDINGS.JSON GENERATED ===")
print(json.dumps(findings, indent=4))
print(f"\nSaved findings to: {FINDINGS_PATH}")