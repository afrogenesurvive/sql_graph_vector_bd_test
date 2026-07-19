# Setup & Run Guide

Complete step-by-step instructions to set up, configure, and run the SQL → Neo4j GraphRAG pipeline.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone & Configure](#2-clone--configure)
3. [Start Neo4j](#3-start-neo4j)
4. [Install Python Dependencies](#4-install-python-dependencies)
5. [Prepare MySQL Data](#5-prepare-mysql-data)
6. [Phase 2 — Migrate SQL → Neo4j](#6-phase-2--migrate-sql--neo4j)
7. [Phase 3.1 — Create Vector Index](#7-phase-31--create-vector-index)
8. [Phase 3.2 — Generate Embeddings](#8-phase-32--generate-embeddings)
9. [Phase 4 — Run Hybrid Queries](#9-phase-4--run-hybrid-queries)
10. [Phase 5 — Verification](#10-phase-5--verification)
11. [Reset & Re-run](#11-reset--re-run)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

| Requirement    | Version | Check Command            |
| -------------- | ------- | ------------------------ |
| Python         | 3.10+   | `python --version`       |
| Docker         | 24+     | `docker --version`       |
| Docker Compose | v2+     | `docker compose version` |
| MySQL          | 8.0+    | `mysql --version`        |

Optional but recommended:

- [Neo4j Browser](http://localhost:7474) (accessible via Docker)
- OpenAI API key (for cloud embeddings; skip for local embeddings)

---

## 2. Clone & Configure

```bash
# 1. Navigate to the project
cd sql_graph_vector_bd_test

# 2. Create your environment file
cp .env.example .env

# 3. Edit .env with your credentials
#    For the sample data, these defaults work:
#      MYSQL_DATABASE=graphrag_demo
#      MYSQL_USER=root
#      MYSQL_PASSWORD=
#
#    To use local embeddings instead of OpenAI:
#      EMBEDDING_PROVIDER=local
#      EMBEDDING_MODEL=all-MiniLM-L6-v2
#      EMBEDDING_DIMENSIONS=384
```

> **⚠️ Important:** If you use the local embedding provider, the vector index must be created with `--dimensions 384` in [Phase 3.1](#7-phase-31--create-vector-index).

---

## 3. Start Neo4j

```bash
# Start Neo4j 5.x with APOC plugin in detached mode
docker compose up -d

# Wait ~10 seconds for Neo4j to fully initialise, then verify:
docker compose logs neo4j --tail 10
```

**Expected output (last line):**

```
neo4j_graphrag  | Started.
```

**Verify in browser:** Open [http://localhost:7474](http://localhost:7474) and log in with:

- Username: `neo4j`
- Password: `strong-password`

**Verify via Cypher** (run in Neo4j Browser):

```cypher
RETURN apoc.version() AS apoc_version;
```

---

## 4. Install Python Dependencies

```bash
# Option A — using uv (fast, recommended)
uv pip install -r requirements.txt

# Option B — using pip
pip install -r requirements.txt
```

**Expected output:**

```
Successfully installed neo4j-5.x.x openai-1.x.x pymysql-1.x.x ...
```

---

## 5. Prepare MySQL Data

### Option A: Use the included sample data

```bash
# Create the database and tables
mysql -u root < sample_data/schema.sql

# Seed with sample rows
mysql -u root graphrag_demo < sample_data/seed.sql

# Verify
mysql -u root graphrag_demo -e "SELECT COUNT(*) AS products FROM products; SELECT COUNT(*) AS customers FROM customers; SELECT COUNT(*) AS orders FROM orders;"
```

**Expected:**

```
+----------+
| products |
+----------+
|        8 |
+----------+

+-----------+
| customers |
+-----------+
|         5 |
+-----------+

+--------+
| orders |
+--------+
|      6 |
+--------+
```

### Option B: Use your own MySQL database

1. Update `.env` with your connection details:
   ```
   MYSQL_HOST=your-host
   MYSQL_PORT=3306
   MYSQL_USER=your-user
   MYSQL_PASSWORD=your-password
   MYSQL_DATABASE=your-database
   ```
2. Ensure your tables have integer primary keys (the ETL uses an `id` column as the merge key).
3. Skip this step if your data is already in place.

---

## 6. Phase 2 — Migrate SQL → Neo4j

```bash
python scripts/etl_migrate.py
```

**Expected output:**

```
═══ Phase 2: ETL Migration ═══
  ──  Discovering tables...
   ✅  4 tables found: products, customers, orders, order_items
  ──  Migrating table 'products' → :Product
   ✅  Migrated 8 rows → :Product
  ──  Migrating table 'customers' → :Customer
   ✅  Migrated 5 rows → :Customer
  ──  Migrating table 'orders' → :Order
   ✅  Migrated 6 rows → :Order
  ──  Migrating table 'order_items' → :OrderItem
   ✅  Migrated 10 rows → :OrderItem
  ──  Creating foreign-key relationships...
   ✅  Created 3 relationship types
  ✅  Migration complete.
```

### Options

| Flag                   | Purpose                       | Example                       |
| ---------------------- | ----------------------------- | ----------------------------- |
| `--tables`             | Migrate specific tables only  | `--tables products customers` |
| `--limit`              | Max rows per table            | `--limit 500`                 |
| `--skip-relationships` | Skip FK relationship creation | `--skip-relationships`        |

### Verify in Neo4j Browser

```cypher
MATCH (n) RETURN labels(n) AS label, count(*) AS count
ORDER BY count DESC;
```

---

## 7. Phase 3.1 — Create Vector Index

```bash
# For OpenAI embeddings (1536 dimensions)
python scripts/create_vector_index.py --label Product --dimensions 1536

# For local embeddings (384 dimensions)
python scripts/create_vector_index.py --label Product --dimensions 384
```

**Expected output:**

```
═══ Phase 3.1: Vector Index ═══
  ──  Creating vector index on :Product...
   ✅  Vector index 'vector_index' created on :Product (dims=1536, similarity=cosine)
```

### Options

| Flag           | Default        | Purpose                                       |
| -------------- | -------------- | --------------------------------------------- |
| `--label`      | `Product`      | Node label to index                           |
| `--dimensions` | `1536`         | Vector dimension (must match embedding model) |
| `--similarity` | `cosine`       | `cosine`, `euclidean`, or `dot`               |
| `--name`       | `vector_index` | Index name                                    |

### Verify

```cypher
SHOW INDEXES;
```

Look for a row with `type = "VECTOR"` and `labelsOrTypes = ["Product"]`.

---

## 8. Phase 3.2 — Generate Embeddings

```bash
# Generate embeddings from Product descriptions
python scripts/generate_embeddings.py --label Product --text-property description
```

**Expected output:**

```
═══ Phase 3.2: Generate Embeddings ═══
  ──  Reading :Product nodes with descriptions...
   ℹ️  8 nodes to embed
  ──  Generating embeddings...
   📊  Progress:    8 /    8  nodes embedded
   ✅  Completed: 8 / 8 nodes embedded
```

### Options

| Flag              | Default       | Purpose                           |
| ----------------- | ------------- | --------------------------------- |
| `--label`         | `Product`     | Node label whose text to embed    |
| `--text-property` | `description` | Property containing text to embed |
| `--batch-size`    | `50`          | Log progress every N nodes        |

### Verify

```cypher
MATCH (n:Product)
WHERE n.embedding IS NOT NULL
RETURN count(*) AS embedded;

-- Inspect an embedding vector
MATCH (n:Product)
WHERE n.embedding IS NOT NULL
RETURN n.name, size(n.embedding) AS vector_size
LIMIT 3;
```

---

## 9. Phase 4 — Run Hybrid Queries

### Interactive mode

```bash
python scripts/hybrid_query.py --pretty
# Enter your query: wireless headphones
```

### One-shot mode

```bash
python scripts/hybrid_query.py --query "affordable electronics" --pretty
```

**Expected output:**

```
═══ Phase 4: Hybrid Query ═══
  ──  Embedding query: 'affordable electronics'...
   ✅  Query embedded (1536 dimensions)
  ──  Running vector search + graph traversal...
   ✅  Returned 5 results

[
  {
    "seed_id": 1,
    "seed_name": "Wireless Bluetooth Headphones",
    "score": 0.87,
    "connected_entities": [
      {"entity": "...", "label": ["OrderItem"], "relationship": "BELONGS_TO_PRODUCT"},
      ...
    ]
  },
  ...
]
```

### Options

| Flag       | Default         | Purpose                  |
| ---------- | --------------- | ------------------------ |
| `--query`  | _(interactive)_ | Search query string      |
| `--label`  | `Product`       | Node label to search     |
| `--top-k`  | `5`             | Number of results        |
| `--index`  | `vector_index`  | Vector index name        |
| `--pretty` | off             | Pretty-print JSON output |

---

## 10. Phase 5 — Verification

Run the full verification suite:

```bash
# 1. Check nodes and counts
docker compose exec neo4j cypher-shell -u neo4j -p strong-password \
  "MATCH (n) RETURN labels(n) AS label, count(*) AS count ORDER BY count DESC"

# 2. Check relationships
docker compose exec neo4j cypher-shell -u neo4j -p strong-password \
  "MATCH ()-[r]->() RETURN type(r) AS rel_type, count(*) AS count"

# 3. Check vector index
docker compose exec neo4j cypher-shell -u neo4j -p strong-password \
  "SHOW INDEXES"

# 4. Check embeddings exist
docker compose exec neo4j cypher-shell -u neo4j -p strong-password \
  "MATCH (n:Product) WHERE n.embedding IS NOT NULL RETURN count(*) AS embedded"
```

---

## 11. Reset & Re-run

To wipe Neo4j and start fresh:

```bash
# Stop and remove the container + volumes
docker compose down -v

# Restart
docker compose up -d

# Re-run the pipeline
python scripts/etl_migrate.py
python scripts/create_vector_index.py
python scripts/generate_embeddings.py
```

---

## 12. Troubleshooting

### Neo4j won't start

```bash
# Check logs
docker compose logs neo4j

# Common fix: remove stale volumes and retry
docker compose down -v
docker compose up -d
```

### APOC not available

```bash
# Verify APOC is listed
docker compose exec neo4j cypher-shell -u neo4j -p strong-password \
  "CALL apoc.help('apoc') YIELD name RETURN name LIMIT 5"
```

If empty, restart with APOC explicitly enabled:

```bash
docker compose down
# Edit docker-compose.yml to ensure NEO4J_PLUGINS includes apoc
docker compose up -d
```

### Vector index creation fails

```cypher
-- Check if an index already exists
SHOW INDEXES;

-- Drop it manually if needed
DROP INDEX vector_index IF EXISTS;
```

### Embedding dimension mismatch

```bash
# Error: Vector dimension 1536 does not match index dimension 384
# Solution: recreate the index with the correct dimensions
python scripts/create_vector_index.py --dimensions 384
```

### "No module named 'scripts'"

```bash
# Run from the project root directory
cd /path/to/sql_graph_vector_bd_test
python scripts/etl_migrate.py
```

### MySQL connection refused

```bash
# Ensure MySQL is running
mysqladmin ping -u root

# Check host/port in .env
grep MYSQL_ .env
```

### OpenAI API errors

```bash
# Verify your API key is set
grep OPENAI_API_KEY .env

# Or switch to local embeddings
# Edit .env:
#   EMBEDDING_PROVIDER=local
#   EMBEDDING_MODEL=all-MiniLM-L6-v2
#   EMBEDDING_DIMENSIONS=384
# Then recreate the vector index with --dimensions 384
```
