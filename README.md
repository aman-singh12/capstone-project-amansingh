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