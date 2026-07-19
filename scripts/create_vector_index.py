"""Phase 3.1: Create a vector index in Neo4j.

Usage:
    python scripts/create_vector_index.py \\
        --label Product \\
        --dimensions 1536 \\
        --similarity cosine
"""

from scripts import config
from scripts.db import get_neo4j_driver
from scripts.logger import get_logger, log_ok, log_step, log_phase

logger = get_logger(__name__)


def create_vector_index(
    label: str = "Product",
    dimensions: int = 1536,
    similarity_fn: str = "cosine",
    name: str = "vector_index",
) -> None:
    """Create a Neo4j vector index for the given label."""
    driver = get_neo4j_driver()

    try:
        # Drop existing index with the same name so this is idempotent
        with driver.session() as session:
            session.run(f"DROP INDEX {name} IF EXISTS")

        from neo4j_graphrag.indexes import create_vector_index as _create

        _create(
            driver,
            name=name,
            label=label,
            embedding_property="embedding",
            dimensions=dimensions,
            similarity_fn=similarity_fn,
        )
        log_ok(
            f"Vector index '{name}' created on :{label} "
            f"(dims={dimensions}, similarity={similarity_fn})"
        )
    finally:
        driver.close()


def main():
    from scripts.logger import setup_logger
    setup_logger()

    import argparse

    parser = argparse.ArgumentParser(
        description="Create a Neo4j vector index"
    )
    parser.add_argument(
        "--label",
        default="Product",
        help="Node label to index (default: Product)",
    )
    parser.add_argument(
        "--dimensions",
        type=int,
        default=config.EMBEDDING_DIMENSIONS,
        help=f"Vector dimensions (default: {config.EMBEDDING_DIMENSIONS})",
    )
    parser.add_argument(
        "--similarity",
        default="cosine",
        choices=["cosine", "euclidean", "dot"],
        help="Similarity function (default: cosine)",
    )
    parser.add_argument(
        "--name",
        default="vector_index",
        help="Index name (default: vector_index)",
    )
    args = parser.parse_args()

    log_phase("3.1", "Vector Index")
    log_step(f"Creating vector index on :{args.label}...")
    create_vector_index(
        label=args.label,
        dimensions=args.dimensions,
        similarity_fn=args.similarity,
        name=args.name,
    )


if __name__ == "__main__":
    main()
