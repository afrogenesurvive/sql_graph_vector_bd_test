# Agent: SQL → Neo4j GraphRAG Pipeline

## Objective

Migrate a PostgreSQL/MySQL database into Neo4j with vector embeddings, enabling hybrid vector + graph (GraphRAG) queries.

## Architecture

```
SQL DB ───► Neo4j (graph + vector index) ───► Hybrid Cypher (SEARCH + MATCH)
                  ▲
                  │
          OpenAI Embeddings
          (text → vector)
```

## Components

- **Source:** PostgreSQL or MySQL
- **Target:** Neo4j 5.x+ (with vector index support)
- **Embeddings:** OpenAI `text-embedding-3-small` (1536d) or local `all-MiniLM-L6-v2` (384d)
- **Migration:** Use Neo4j's `apoc.load.jdbc` + custom Python ETL (not SQL2Graph — that targets Memgraph)

---

## Phase 1: Environment Setup

### 1.1 Prerequisites

- Python 3.10+
- Docker
- Neo4j APOC plugin (for JDBC import from SQL)
- OpenAI API key (for cloud embeddings)

### 1.2 Start Neo4j

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/strong-password \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:5
```

Verify at http://localhost:7474. Install APOC if not auto-installed.

### 1.3 Install Python Dependencies

```bash
uv pip install "neo4j>=5.0" "openai>=1.0" python-dotenv pandas
```

---

## Phase 2: Migrate SQL Data to Neo4j

### 2.1 Strategy: Custom Python ETL

Skip SQL2Graph (it generates Memgraph Cypher, not Neo4j-compatible). Instead, write a Python script that:

1. Reads tables from SQL via `psycopg2` / `pymysql`
2. Creates nodes with labels matching table names
3. Creates relationships based on foreign keys
4. Sets column values as node properties

```python
# etl_migrate.py
import os
import psycopg2
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# SQL connection
sql_conn = psycopg2.connect(os.getenv("SQL_CONNECTION_STRING"))

# Neo4j connection
neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD"))
)

def migrate_table(table_name, label=None):
    """Migrate a SQL table to Neo4j node label."""
    label = label or table_name.title()
    cursor = sql_conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 1000")
    columns = [desc[0] for desc in cursor.description]

    with neo4j_driver.session() as session:
        for row in cursor.fetchall():
            props = dict(zip(columns, row))
            node_id = props.pop("id", None)
            session.run(
                f"MERGE (n:{label} {{id: $id}}) SET n += $props",
                id=node_id, props=props
            )
    print(f"Migrated {table_name} → :{label}")

# Usage example:
# migrate_table("products", "Product")
# migrate_table("customers", "Customer")
```

### 2.2 Migration Steps

1. List all tables in SQL: `SELECT table_name FROM information_schema.tables`
2. Identify foreign key relationships
3. Migrate each table with `migrate_table()`
4. Create relationships based on foreign keys

### 2.3 Success Criteria

```cypher
// In Neo4j Browser
MATCH (n) RETURN labels(n) AS label, count(*) AS count;
MATCH ()-[r]->() RETURN type(r) AS rel_type, count(*) AS count;
```

---

## Phase 3: Generate & Store Embeddings

### 3.1 Create Vector Index

```python
# create_vector_index.py
from neo4j import GraphDatabase
from neo4j_graphrag.indexes import create_vector_index
from dotenv import load_dotenv
import os

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

create_vector_index(
    driver,
    name="vector_index",
    label="Product",              # Adjust to your domain label
    embedding_property="embedding",
    dimensions=1536,
    similarity_fn="cosine",
)
driver.close()
```

### 3.2 Generate Embeddings from Neo4j (Not SQL)

Read text properties from **existing Neo4j nodes** — the data is already there after Phase 2.

```python
# generate_embeddings.py
import os
from neo4j import GraphDatabase
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Modern OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = "text-embedding-3-small"

neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

def embed_text(text: str) -> list[float]:
    response = client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def generate_embeddings(label: str, text_property: str):
    """Fetch nodes with text, generate embeddings, store them."""
    with neo4j_driver.session() as session:
        nodes = session.run(
            f"MATCH (n:{label}) WHERE n.{text_property} IS NOT NULL "
            "RETURN elementId(n) AS id, n.{text_property} AS text"
        )
        for record in nodes:
            node_id = record["id"]
            text = record["text"]
            embedding = embed_text(text)
            session.run(
                "MATCH (n) WHERE elementId(n) = $id "
                "SET n.embedding = $embedding",
                id=node_id, embedding=embedding
            )

# Usage:
# generate_embeddings("Product", "description")
```

### 3.3 Verify

```cypher
MATCH (n:Product)
WHERE n.embedding IS NOT NULL
RETURN count(*) AS embedded_count
LIMIT 1;
```

---

## Phase 4: Hybrid Vector + Graph Query

### 4.1 Query Function

```python
# hybrid_query.py
import os
import json
from neo4j import GraphDatabase
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K = 5

neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

def hybrid_search(user_query: str, label: str = "Product"):
    # Step 1: Embed query
    response = client.embeddings.create(
        input=user_query,
        model=EMBEDDING_MODEL
    )
    query_embedding = response.data[0].embedding

    # Step 2: Vector search + graph traversal (single Cypher query)
    with neo4j_driver.session() as session:
        results = session.run(f"""
            MATCH (seed:{label})
              SEARCH seed IN (
                VECTOR INDEX vector_index
                FOR $embedding
                LIMIT $top_k
              ) SCORE AS score
            OPTIONAL MATCH (seed)-[r]-(connected)
            RETURN
                seed.id AS seed_id,
                seed.name AS seed_name,
                score,
                collect(DISTINCT {{
                    entity: elementId(connected),
                    label: labels(connected),
                    relationship: type(r)
                }}) AS connected_entities
            ORDER BY score DESC
            LIMIT $top_k
        """, embedding=query_embedding, top_k=TOP_K)

        return [dict(r) for r in results]

if __name__ == "__main__":
    query = input("Enter your query: ")
    results = hybrid_search(query)
    print(json.dumps(results, indent=2, default=str))
```

### 4.2 Fallback (for older Neo4j versions)

If `SEARCH` syntax is unavailable, use the procedure-based approach:

```cypher
CALL db.index.vector.queryNodes('vector_index', $top_k, $embedding)
YIELD node AS seed, score
OPTIONAL MATCH (seed)-[r]-(connected)
RETURN seed.id, seed.name, score, collect(...)
```

---

## Phase 5: Verification

```cypher
-- Vector search test
CALL db.index.vector.queryNodes('vector_index', 5, $test_embedding)
YIELD node, score
RETURN node.name, score;
```

Run `hybrid_query.py` with sample queries. Verify results include both vector-matched nodes and their graph-connected neighbors.

---

## Configuration (.env)

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=strong-password
OPENAI_API_KEY=sk-...
SQL_CONNECTION_STRING=postgresql://user:password@localhost:5432/mydb
```

---

## Command Reference

| Phase | Command                                  | Purpose                     |
| ----- | ---------------------------------------- | --------------------------- |
| 1.2   | `docker run -d --name neo4j ... neo4j:5` | Start Neo4j                 |
| 2.1   | `python etl_migrate.py`                  | Migrate SQL → Neo4j         |
| 3.1   | `python create_vector_index.py`          | Create vector index         |
| 3.2   | `python generate_embeddings.py`          | Generate & store embeddings |
| 4     | `python hybrid_query.py`                 | Run hybrid query            |

## Common Pitfalls

| Issue                         | Fix                                                                  |
| ----------------------------- | -------------------------------------------------------------------- |
| Embedding dimension mismatch  | Ensure `create_vector_index(dimensions=...)` matches your model      |
| `openai` `AttributeError`     | Use `client.embeddings.create()`, not `openai.Embedding.create()`    |
| `SEARCH` syntax error         | Upgrade to Neo4j 5.x or use `db.index.vector.queryNodes()` procedure |
| Data not found for embedding  | Read text from Neo4j, not back from SQL                              |
| No results from vector search | Verify `embedding` property exists on nodes and index is populated   |
