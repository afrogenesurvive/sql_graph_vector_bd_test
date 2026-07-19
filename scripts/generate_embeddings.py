"""Phase 3.2: Generate and store vector embeddings for Neo4j nodes.

Reads text properties from existing Neo4j nodes, generates embeddings
via the configured provider, and writes them back to the ``embedding``
property on each node.
"""

from typing import List, Optional

from scripts import config
from scripts.db import get_neo4j_driver
from scripts.embedder import get_embedding
from scripts.logger import get_logger, log_ok, log_step, log_warn, log_progress, log_phase, log_info

logger = get_logger(__name__)


def generate_embeddings(
    label: str,
    text_property: str = "description",
    batch_size: int = 50,
) -> int:
    """Generate embeddings for all nodes of *label* that have *text_property*.

    Returns the number of nodes updated.
    """
    driver = get_neo4j_driver()
    updated = 0

    try:
        with driver.session() as session:
            result = session.run(
                f"MATCH (n:{label}) "
                f"WHERE n.`{text_property}` IS NOT NULL "
                "RETURN elementId(n) AS id, n.`%s` AS text" % text_property
            )
            nodes = list(result)

            if not nodes:
                log_warn(
                    f"No :{label} nodes found with a non-null `{text_property}` property."
                )
                return 0

            log_info(f"{len(nodes)} nodes to embed")

            for i, record in enumerate(nodes, 1):
                node_id = record["id"]
                text: str = record["text"]

                if not text or not text.strip():
                    continue

                embedding = get_embedding(text.strip())

                session.run(
                    "MATCH (n) WHERE elementId(n) = $id "
                    "SET n.embedding = $embedding",
                    id=node_id,
                    embedding=embedding,
                )
                updated += 1

                if i % batch_size == 0 or i == len(nodes):
                    log_progress(i, len(nodes), f"{label.lower()} nodes")

            log_ok(f"Completed: {updated} / {len(nodes)} nodes embedded.")
    finally:
        driver.close()

    return updated


def main():
    from scripts.logger import setup_logger
    setup_logger()

    import argparse

    parser = argparse.ArgumentParser(
        description="Generate and store vector embeddings in Neo4j"
    )
    parser.add_argument(
        "--label",
        default="Product",
        help="Node label to embed (default: Product)",
    )
    parser.add_argument(
        "--text-property",
        default="description",
        help="Property containing text to embed (default: description)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Log progress every N nodes (default: 50)",
    )
    args = parser.parse_args()

    log_phase("3.2", "Generate Embeddings")
    log_step(f"Reading :{args.label} nodes with `{args.text_property}`...")
    generate_embeddings(
        label=args.label,
        text_property=args.text_property,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
