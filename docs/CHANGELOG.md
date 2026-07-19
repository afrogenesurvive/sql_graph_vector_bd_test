# Changelog

## [0.1.0] — 2026-07-19

### Added

- Initial project scaffold: Docker Compose (Neo4j 5 + APOC), Python scripts, sample data
- **Phase 1:** Neo4j container with APOC plugin via `docker compose up -d`
- **Phase 2:** ETL migration script (`scripts/etl_migrate.py`) — migrates MySQL tables to Neo4j nodes and foreign-key relationships
- **Phase 3.1:** Vector index creation script (`scripts/create_vector_index.py`) — configurable label, dimensions, similarity metric
- **Phase 3.2:** Embedding generation script (`scripts/generate_embeddings.py`) — supports OpenAI and local (all-MiniLM-L6-v2) embedding providers
- **Phase 4:** Hybrid query script (`scripts/hybrid_query.py`) — vector search + graph traversal with Cypher
- Central configuration (`scripts/config.py`) with `.env` support
- Database connection factories (`scripts/db.py`) for Neo4j and MySQL
- Embedding client abstraction (`scripts/embedder.py`) with OpenAI and SentenceTransformers backends
- Sample e-commerce schema and seed data (`sample_data/`)
- Comprehensive documentation: `docs/setup_and_run.md`, `docs/system_architecture.md`, `docs/agent_instructions.md`
- `README.md` with project overview, architecture diagram, quick-start, and configuration reference
- `.env.example` and `.gitignore` for environment setup
