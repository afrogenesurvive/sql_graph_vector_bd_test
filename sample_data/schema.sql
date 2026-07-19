-- Sample e-commerce schema for the SQL → Neo4j GraphRAG pipeline.
-- Run against MySQL:  mysql -u root < sample_data/schema.sql

CREATE DATABASE IF NOT EXISTS graphrag_demo;
USE graphrag_demo;

-- ── Products ────────────────────────────────────────────
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(200)    NOT NULL,
    description TEXT,
    price       DECIMAL(10, 2)  NOT NULL,
    category    VARCHAR(100)    NOT NULL,
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ── Customers ───────────────────────────────────────────
CREATE TABLE customers (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(200)    NOT NULL,
    email       VARCHAR(200)    NOT NULL UNIQUE,
    city        VARCHAR(100)    NOT NULL,
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ── Orders ──────────────────────────────────────────────
CREATE TABLE orders (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT             NOT NULL,
    order_date  DATE            NOT NULL,
    total       DECIMAL(12, 2)  NOT NULL DEFAULT 0.00,
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- ── Order Items ─────────────────────────────────────────
CREATE TABLE order_items (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    order_id    INT             NOT NULL,
    product_id  INT             NOT NULL,
    quantity    INT             NOT NULL DEFAULT 1,
    unit_price  DECIMAL(10, 2)  NOT NULL,
    FOREIGN KEY (order_id)   REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
