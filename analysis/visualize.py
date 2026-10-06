import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# Mamaearth Returns & Growth Intelligence Pipeline
# Visualization Layer
# ============================================================

# Create output directory
output_dir = Path("visualizations")
output_dir.mkdir(exist_ok=True)

# ------------------------------------------------------------
# Load raw data
# ------------------------------------------------------------

customers = pd.read_csv("data/customers.csv")
products = pd.read_csv("data/products.csv")
orders = pd.read_csv("data/orders.csv")

# Clean payment method
orders["payment_method"] = (
    orders["payment_method"]
    .str.strip()
    .str.upper()
)

# Convert missing values
orders["discount_pct"] = pd.to_numeric(
    orders["discount_pct"],
    errors="coerce"
).fillna(0)

orders["rating"] = pd.to_numeric(
    orders["rating"],
    errors="coerce"
)

# ------------------------------------------------------------
# Remove duplicate orders
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

orders = orders.drop_duplicates(
    subset=duplicate_key,
    keep="first"
).copy()

# Impute rating
orders["rating"] = orders["rating"].fillna(
    orders["rating"].median()
)

# ------------------------------------------------------------
# Merge data
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

# Calculate order value
df["order_value"] = (
    df["quantity"]
    * df["price"]
    * (1 - df["discount_pct"] / 100.0)
)

# ============================================================
# VISUALIZATION 1
# Return Rate by Payment Method
# ============================================================

return_rate = (
    df.groupby("payment_method")["returned"]
    .mean()
    .mul(100)
    .sort_values(ascending=False)
)

plt.figure(figsize=(8, 5))

ax = return_rate.plot(kind="bar")

plt.title("COD Has the Highest Return Rate")
plt.xlabel("Payment Method")
plt.ylabel("Return Rate (%)")
plt.xticks(rotation=0)

for container in ax.containers:
    ax.bar_label(
        container,
        fmt="%.1f%%",
        padding=3
    )

plt.tight_layout()

return_path = output_dir / "return_rate_by_payment.png"
plt.savefig(return_path, dpi=300, bbox_inches="tight")
plt.close()

print(f"Saved: {return_path}")


# ============================================================
# VISUALIZATION 2
# Corrected Monthly Revenue Trend
# ============================================================

# Convert dates
df["order_date"] = pd.to_datetime(df["order_date"])

# Detect quantity outliers using IQR
q1 = df["quantity"].quantile(0.25)
q3 = df["quantity"].quantile(0.75)
iqr = q3 - q1

lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

df["quantity_outlier"] = (
    (df["quantity"] < lower_bound)
    | (df["quantity"] > upper_bound)
)

# Remove flagged quantity outliers for corrected revenue
corrected_df = df.loc[
    ~df["quantity_outlier"]
].copy()

monthly_revenue = (
    corrected_df
    .groupby(
        corrected_df["order_date"].dt.to_period("M")
    )["order_value"]
    .sum()
)

plt.figure(figsize=(9, 5))

ax = monthly_revenue.plot(
    kind="line",
    marker="o"
)

plt.title("March Is the True Revenue Peak After Outlier Correction")
plt.xlabel("Month")
plt.ylabel("Revenue (₹)")
plt.xticks(rotation=45)

# Highlight exact values on the line
for x, y in enumerate(monthly_revenue):
    ax.annotate(
        f"₹{y:,.0f}",
        (x, y),
        textcoords="offset points",
        xytext=(0, 8),
        ha="center"
    )

plt.tight_layout()

monthly_path = output_dir / "monthly_revenue_trend.png"
plt.savefig(monthly_path, dpi=300, bbox_inches="tight")
plt.close()

print(f"Saved: {monthly_path}")

print("\nVisualization generation completed successfully.")