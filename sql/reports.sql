-- Masai Mamaearth Returns & Growth Intelligence Pipeline
-- SQL reporting layer
--
-- All revenue calculations use:
-- quantity * price * (1 - discount_pct / 100.0)
--
-- Expected outputs are included as comments for verification.

PRAGMA foreign_keys = ON;


-- ============================================================
-- REPORT A: Order count, total revenue, and average order value
-- ============================================================

-- Expected:
-- order_count = 180
-- total_revenue = 99860.20
-- average_order_value = 554.78

SELECT
    COUNT(*) AS order_count,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS total_revenue,
    ROUND(
        AVG(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS average_order_value
FROM orders o
JOIN products p
    ON o.product_id = p.product_id;


-- ============================================================
-- REPORT B: Rated vs unrated orders
-- ============================================================

-- Expected:
-- total_orders = 180
-- rated_orders = 165
-- unrated_orders = 15

SELECT
    COUNT(*) AS total_orders,
    COUNT(rating) AS rated_orders,
    COUNT(*) - COUNT(rating) AS unrated_orders
FROM orders;


-- ============================================================
-- REPORT C: Customers with zero orders
-- LEFT JOIN method
-- ============================================================

-- Expected:
-- C045 | Vihaan

SELECT
    c.customer_id,
    c.name
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
WHERE o.customer_id IS NULL
ORDER BY c.customer_id;


-- ============================================================
-- REPORT C2: Customers with zero orders
-- NOT IN method
-- ============================================================

-- Expected:
-- C045 | Vihaan

SELECT
    customer_id,
    name
FROM customers
WHERE customer_id NOT IN (
    SELECT customer_id
    FROM orders
)
ORDER BY customer_id;


-- ============================================================
-- REPORT D: City return rate greater than 20%
-- ============================================================

-- Expected:
-- Jaipur     | 19 | 8  | 42.1
-- Lucknow    | 49 | 15 | 30.6
-- Bangalore  | 33 | 8  | 24.2

SELECT
    c.city,
    COUNT(*) AS total_orders,
    SUM(o.returned) AS returned_orders,
    ROUND(
        100.0 * SUM(o.returned) / COUNT(*),
        1
    ) AS return_rate_pct
FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING 100.0 * SUM(o.returned) / COUNT(*) > 20
ORDER BY return_rate_pct DESC;


-- ============================================================
-- REPORT E: Customer revenue ranking
-- ============================================================

-- Expected top 5:
-- C043 | Reyansh | 12920.00
-- C026 | Isha    | 8371.60
-- C008 | Meera   | 4564.60
-- C011 | Arjun   | 4111.00
-- C042 | Sanya   | 3785.00

SELECT
    c.customer_id,
    c.name,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS total_revenue
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN products p
    ON o.product_id = p.product_id
GROUP BY c.customer_id, c.name
ORDER BY total_revenue DESC;


-- ============================================================
-- REPORT E2: Customer revenue ranks 3 to 5
-- LIMIT 3 OFFSET 2
-- ============================================================

-- Expected:
-- C008 | Meera | 4564.60
-- C011 | Arjun | 4111.00
-- C042 | Sanya | 3785.00

SELECT
    c.customer_id,
    c.name,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS total_revenue
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN products p
    ON o.product_id = p.product_id
GROUP BY c.customer_id, c.name
ORDER BY total_revenue DESC
LIMIT 3 OFFSET 2;


-- ============================================================
-- REPORT F: Revenue by product category
-- ============================================================

-- Expected:
-- Haircare        | 54 | 44956.10
-- Skincare        | 60 | 27346.00
-- Babycare        | 30 | 16805.00
-- PersonalCare    | 36 | 10753.10

SELECT
    p.category,
    COUNT(*) AS order_count,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS category_revenue
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY category_revenue DESC;


-- ============================================================
-- REPORT G: Customers whose names begin with A
-- ============================================================

-- Expected: 10 customers

SELECT
    customer_id,
    name
FROM customers
WHERE name LIKE 'A%'
ORDER BY name;


-- ============================================================
-- REPORT H: Acquisition sources
-- ============================================================

-- Expected sources:
-- Ad
-- Organic
-- Referral
-- Social

SELECT DISTINCT
    acquisition_source
FROM customers
ORDER BY acquisition_source;


-- ============================================================
-- REPORT I: Loyalty tier
-- ============================================================

-- Rule:
-- city_tier = 1  -> Gold
-- city_tier != 1 -> Silver

-- Expected:
-- Gold   | 28
-- Silver | 17

SELECT
    CASE
        WHEN city_tier = 1 THEN 'Gold'
        ELSE 'Silver'
    END AS loyalty_tier,
    COUNT(*) AS customer_count
FROM customers
GROUP BY
    CASE
        WHEN city_tier = 1 THEN 'Gold'
        ELSE 'Silver'
    END
ORDER BY loyalty_tier;