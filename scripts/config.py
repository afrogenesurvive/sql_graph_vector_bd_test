"""Central configuration loader — single import point for all scripts."""

import os
from dotenv import load_dotenv

load_dotenv()


# ── Neo4j ──────────────────────────────────────────────
NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "strong-password")

# ── MySQL ──────────────────────────────────────────────
MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "mydb")

# ── Embeddings ─────────────────────────────────────────
EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "openai")  # "openai" | "local"
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

# ── OpenAI ─────────────────────────────────────────────
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

# ── Query ──────────────────────────────────────────────
TOP_K: int = int(os.getenv("TOP_K", "5"))


def mysql_connection_string() -> str:
    """Build a PyMySQL connection string from config."""
    return (
        f"host={MYSQL_HOST},"
        f"port={MYSQL_PORT},"
        f"user={MYSQL_USER},"
        f"password={MYSQL_PASSWORD},"
        f"database={MYSQL_DATABASE}"
    )
