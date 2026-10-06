-- Masai Mamaearth Returns & Growth Intelligence Pipeline capstone project
-- Seed data loader for SQLite
-- Run this script from the repository root.
--
-- Raw CSV files are intentionally NOT modified.
-- Cleaning is performed later in Python.

PRAGMA foreign_keys = ON;

-- Clear existing data so the loader can be safely re-run.
DELETE FROM orders;
DELETE FROM products;
DELETE FROM customers;

-- Load customers
.mode csv
.import --skip 1 data/customers.csv customers

-- Load products
.mode csv
.import --skip 1 data/products.csv products

-- Load orders
.mode csv
.import --skip 1 data/orders.csv orders

-- SQLite imports blank CSV cells as empty strings.
-- Convert those deliberate missing values to SQL NULL.
UPDATE orders
SET discount_pct = NULL
WHERE discount_pct = '';

UPDATE orders
SET rating = NULL
WHERE rating = '';

-- Verification
SELECT 'customers' AS table_name, COUNT(*) AS row_count
FROM customers;

SELECT 'products' AS table_name, COUNT(*) AS row_count
FROM products;

SELECT 'orders' AS table_name, COUNT(*) AS row_count
FROM orders;
