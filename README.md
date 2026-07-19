# SQL → Neo4j GraphRAG Pipeline

Migrate a MySQL database into Neo4j with vector embeddings, enabling hybrid vector + graph (GraphRAG) queries.

## Architecture

```
MySQL ───► Neo4j (graph + vector index) ───► Hybrid Cypher (SEARCH + MATCH)
                  ▲
                  │
          OpenAI / all-MiniLM-L6-v2
          (text → vector)
```

## Prerequisites

- Python 3.10+
- Docker
- MySQL database (or use the included sample data)
- OpenAI API key (if using cloud embeddings)

## Quick Start

```bash
# 1. Start Neo4j
docker compose up -d

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Install dependencies
uv pip install -r requirements.txt
# or: pip install -r requirements.txt

# 4. Load sample data (optional)
mysql -u root < sample_data/schema.sql
mysql -u root < sample_data/seed.sql

# 5. Run the pipeline
python scripts/etl_migrate.py
python scripts/create_vector_index.py
python scripts/generate_embeddings.py
python scripts/hybrid_query.py --query "your search query"
```

## Pipeline Phases

| Phase | Script                           | Purpose                                            |
| ----- | -------------------------------- | -------------------------------------------------- |
| 1     | `docker compose up -d`           | Start Neo4j with APOC                              |
| 2     | `scripts/etl_migrate.py`         | Migrate MySQL tables → Neo4j nodes + relationships |
| 3.1   | `scripts/create_vector_index.py` | Create vector index on a label                     |
| 3.2   | `scripts/generate_embeddings.py` | Generate & store vector embeddings                 |
| 4     | `scripts/hybrid_query.py`        | Run hybrid vector + graph queries                  |

## Project Structure

```
├── .env.example          # Configuration template
├── .gitignore
├── docker-compose.yml    # Neo4j 5 + APOC
├── requirements.txt       # Python dependencies
├── scripts/
│   ├── config.py          # Central config loader
│   ├── db.py              # Neo4j + MySQL connection factories
│   ├── embedder.py        # Embedding client (OpenAI / local)
│   ├── etl_migrate.py     # Phase 2: SQL → Neo4j ETL
│   ├── create_vector_index.py  # Phase 3.1: Vector index
│   ├── generate_embeddings.py  # Phase 3.2: Embeddings
│   └── hybrid_query.py    # Phase 4: Hybrid search
├── sample_data/
│   ├── schema.sql         # MySQL e-commerce schema
│   └── seed.sql           # Sample data rows
└── docs/
    └── agent_instructions.md
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

| Variable               | Description                 | Default                  |
| ---------------------- | --------------------------- | ------------------------ |
| `NEO4J_URI`            | Neo4j Bolt URI              | `bolt://localhost:7687`  |
| `NEO4J_USER`           | Neo4j username              | `neo4j`                  |
| `NEO4J_PASSWORD`       | Neo4j password              | `strong-password`        |
| `MYSQL_HOST`           | MySQL host                  | `localhost`              |
| `MYSQL_PORT`           | MySQL port                  | `3306`                   |
| `MYSQL_USER`           | MySQL user                  | `root`                   |
| `MYSQL_PASSWORD`       | MySQL password              |                          |
| `MYSQL_DATABASE`       | MySQL database name         | `mydb`                   |
| `EMBEDDING_PROVIDER`   | `openai` or `local`         | `openai`                 |
| `EMBEDDING_MODEL`      | Embedding model name        | `text-embedding-3-small` |
| `EMBEDDING_DIMENSIONS` | Embedding vector dimensions | `1536`                   |
| `OPENAI_API_KEY`       | OpenAI API key              |                          |
| `TOP_K`                | Default top-K results       | `5`                      |

## Verification

```cypher
-- In Neo4j Browser (http://localhost:7474)
MATCH (n) RETURN labels(n) AS label, count(*) AS count;
MATCH ()-[r]->() RETURN type(r) AS rel_type, count(*) AS count;
CALL db.index.vector.queryNodes('vector_index', 5, $embedding) YIELD node, score RETURN node.name, score;
```
