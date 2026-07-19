-- Sample data for the e-commerce schema.
-- Run after schema.sql:  mysql -u root graphrag_demo < sample_data/seed.sql

USE graphrag_demo;

-- ── Products ────────────────────────────────────────────
INSERT INTO products (name, description, price, category) VALUES
('Wireless Bluetooth Headphones',
 'Noise-cancelling over-ear headphones with 30-hour battery life and premium sound quality.',
 89.99, 'Electronics'),
('Stainless Steel Water Bottle',
 'Double-wall insulated 750ml water bottle. Keeps drinks cold for 24 hours or hot for 12.',
 24.95, 'Home & Kitchen'),
('Ergonomic Office Chair',
 'Adjustable lumbar support, breathable mesh back, and 4D armrests for all-day comfort.',
 349.00, 'Furniture'),
('Organic Green Tea Collection',
 'Set of 4 premium organic green teas: Jasmine, Matcha, Sencha, and Genmaicha.',
 28.50, 'Groceries'),
('USB-C Hub 7-in-1',
 'Compact USB-C hub with HDMI 4K, SD/microSD, USB 3.0, and 100W power delivery.',
 45.99, 'Electronics'),
('Yoga Mat Premium',
 'Extra thick 6mm non-slip yoga mat with carrying strap. Eco-friendly TPE material.',
 39.99, 'Sports & Outdoors'),
('The Art of Clean Code',
 'A practical guide to writing maintainable, readable, and efficient Python code.',
 34.99, 'Books'),
('Scented Candle Set',
 'Set of 3 soy wax candles: Vanilla, Lavender, and Cedar. 40-hour burn time each.',
 22.00, 'Home & Kitchen');

-- ── Customers ───────────────────────────────────────────
INSERT INTO customers (name, email, city) VALUES
('Alice Johnson',   'alice@example.com',   'New York'),
('Bob Smith',       'bob@example.com',     'San Francisco'),
('Carol Martinez',  'carol@example.com',   'Chicago'),
('David Lee',       'david@example.com',   'Austin'),
('Emma Wilson',     'emma@example.com',    'Seattle');

-- ── Orders ──────────────────────────────────────────────
INSERT INTO orders (id, customer_id, order_date, total) VALUES
(101, 1, '2026-06-15', 135.94),
(102, 2, '2026-06-20', 73.99),
(103, 3, '2026-07-01', 349.00),
(104, 1, '2026-07-05', 56.50),
(105, 4, '2026-07-10', 124.98),
(106, 5, '2026-07-12', 22.00);

-- ── Order Items ─────────────────────────────────────────
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(101, 1, 1, 89.99),
(101, 5, 1, 45.95),
(102, 5, 1, 45.99),
(102, 2, 1, 24.95),
(103, 3, 1, 349.00),
(104, 4, 1, 28.50),
(104, 7, 1, 34.99),
(105, 1, 1, 89.99),
(105, 6, 1, 39.99),
(106, 8, 1, 22.00);
