# Mamaearth Returns & Growth Intelligence Pipeline

## 1. Project Overview

This capstone project builds an end-to-end data analytics pipeline to understand:

- Where product returns are coming from
- How payment method relates to returns
- How customer and city characteristics relate to return risk
- What the true revenue picture looks like after data cleaning
- How GenAI can convert verified analytical findings into an executive narrative

The project combines SQL, Python, data visualization, and GenAI into a single reproducible workflow.

---

## 2. Business Problem

The raw order data contains several data-quality issues, including:

- Duplicate order records
- Inconsistent payment-method casing
- Missing discount values
- Missing customer ratings
- Quantity outliers

These issues can distort revenue reporting and return analysis.

The objective is therefore to clean and validate the data before using it for business decisions.

---

## 3. Project Objective

The pipeline answers the following questions:

1. What is the total revenue in the raw dataset?
2. How many orders are rated and unrated?
3. Which customers have no orders?
4. Which cities have return rates above 20%?
5. Which customers generate the most revenue?
6. Which product categories generate the most revenue?
7. What acquisition sources exist?
8. What loyalty tiers exist?
9. Which payment method has the highest return rate?
10. Which payment-method and city-tier combination has the highest return risk?
11. What is the true monthly revenue trend after correcting for quantity outliers?
12. Can verified findings be converted into an executive GenAI narrative?

---

## 4. Dataset

The project uses three raw CSV files:

- `customers.csv`
- `products.csv`
- `orders.csv`

The raw files are preserved without manual modification.

Initial dataset sizes:

| Dataset | Rows |
|---|---:|
| Customers | 45 |
| Products | 16 |
| Orders | 180 |

---

## 5. Pipeline Architecture

```text
Raw CSV Data
     |
     v
SQL Relational Layer
     |
     v
SQL Business Reports
     |
     v
Python Cleaning + EDA
     |
     v
Data Visualizations
     |
     v
Verified Findings
     |
     v
GenAI Executive Narrative
```

## 6. Reproducible Run Order

Run the pipeline in the following order from the project root.

### 1. Install dependencies

```text
pip install -r requirements.txt
```

### 2. Run SQL analysis

Execute the SQL files in this order:

```text
sql/schema.sql
sql/seed_data.sql
sql/reports.sql
```

### 3. Run Python cleaning and EDA

```text
python analysis/clean_and_eda.py
```

This step:

- Loads the raw CSV files
- Validates dataset shapes
- Standardizes payment methods
- Removes duplicate orders
- Handles missing discount and rating values
- Calculates cleaned revenue
- Reconciles raw and cleaned revenue
- Detects quantity outliers
- Calculates return rates
- Calculates payment-method × city-tier return rates
- Generates the monthly revenue analysis
- Generates the verified `findings.json`

The verified findings are saved to:

```text
narrator/findings.json
```

### 4. Generate visualizations

```text
python analysis/visualize.py
```

The required charts are saved in:

```text
visualizations/
```

### 5. Run the GenAI narrator

```text
python narrator/generate_narrative.py
```

The narrator reads the verified:

```text
narrator/findings.json
```

and generates an executive Situation-Complication-Resolution narrative.

The generated sample narrative is automatically saved to:

```text
narrator/sample_output.txt
```

---

## 7. GenAI and Offline Fallback

The narrator supports Gemini through the `google-genai` package.

If the `GEMINI_API_KEY` environment variable is available, the program attempts to generate the executive narrative using Gemini.

If the API key is unavailable or the Gemini request fails, the program automatically uses a deterministic offline fallback narrative.

This allows the complete pipeline to run without requiring a Gemini API key.

The narrator also performs numeric accuracy validation against the verified findings before saving the sample output.

---

## 8. Key Verified Findings

The cleaned analysis produces the following key findings:

- Raw revenue: ₹99,860.20
- Cleaned revenue: ₹97,358.30
- Revenue reconciliation difference: ₹2,501.90
- Raw orders: 180
- Cleaned orders: 175
- COD return rate: 44.4%
- Highest-risk segment: COD + City Tier 2
- Highest-risk segment return rate: 54.5%
- True revenue peak: March 2026
- True peak revenue: ₹20,318.90
- Outlier-inflated month: January 2026
- January apparent revenue: ₹29,582.10
- January corrected revenue: ₹11,637.10

---

## 9. Complete Pipeline

```text
SQL
  |
  v
Python Cleaning + EDA
  |
  v
findings.json
  |
  v
GenAI / Offline Narrator
  |
  v
sample_output.txt
```

---

## 10. Project Structure

```text
capstone-project-amansingh/
|
├── README.md
├── requirements.txt
|
├── analysis/
│   ├── clean_and_eda.py
│   └── visualize.py
|
├── data/
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
|
├── narrator/
│   ├── findings.json
│   ├── generate_narrative.py
│   └── sample_output.txt
|
├── sql/
│   ├── schema.sql
│   ├── seed_data.sql
│   └── reports.sql
|
└── visualizations/
    ├── return_rate_by_payment.png
    └── monthly_revenue_trend.png
```
