"""Phase 4: Hybrid vector + graph query.

Embeds a user query, performs a vector search in Neo4j, then traverses
the graph neighborhood of each match to return enriched results.
"""

import json
from typing import Any, Dict, List

from scripts import config
from scripts.db import get_neo4j_driver
from scripts.embedder import get_embedding
from scripts.logger import get_logger, log_ok, log_step, log_phase

logger = get_logger(__name__)


def hybrid_search(
    user_query: str,
    label: str = "Product",
    top_k: int = 5,
    index_name: str = "vector_index",
) -> List[Dict[str, Any]]:
    """Run a hybrid vector + graph search.

    1. Embed *user_query* using the configured embedding provider.
    2. Run a vector search on *index_name* for *label* nodes.
    3. For each match, traverse to connected nodes.
    4. Return enriched results.
    """
    log_step(f"Embedding query: '{user_query}'...")
    query_embedding = get_embedding(user_query)

    driver = get_neo4j_driver()

    try:
        with driver.session() as session:
            # Try SEARCH syntax (Neo4j 5.x+)
            try:
                results = session.run(
                    f"""
                    MATCH (seed:{label})
                      SEARCH seed IN (
                        VECTOR INDEX `{index_name}`
                        FOR $embedding
                        LIMIT $top_k
                      ) SCORE AS score
                    OPTIONAL MATCH (seed)-[r]-(connected)
                    RETURN
                        seed.id AS seed_id,
                        coalesce(seed.name, seed.title) AS seed_name,
                        score,
                        collect(DISTINCT {{
                            entity: elementId(connected),
                            label: labels(connected),
                            relationship: type(r)
                        }}) AS connected_entities
                    ORDER BY score DESC
                    LIMIT $top_k
                    """,
                    embedding=query_embedding,
                    top_k=top_k,
                )
                log_ok(f"Returned {len(results)} results")
                return [dict(r) for r in results]

            except Exception:
                # Fallback: procedure-based approach for older Neo4j
                log_step("SEARCH syntax unavailable; trying procedure-based fallback...")
                results = session.run(
                    f"""
                    CALL db.index.vector.queryNodes('{index_name}', $top_k, $embedding)
                    YIELD node AS seed, score
                    OPTIONAL MATCH (seed)-[r]-(connected)
                    RETURN
                        seed.id AS seed_id,
                        coalesce(seed.name, seed.title) AS seed_name,
                        score,
                        collect(DISTINCT {{
                            entity: elementId(connected),
                            label: labels(connected),
                            relationship: type(r)
                        }}) AS connected_entities
                    ORDER BY score DESC
                    LIMIT $top_k
                    """,
                    embedding=query_embedding,
                    top_k=top_k,
                )
                return [dict(r) for r in results]

    finally:
        driver.close()


def main():
    from scripts.logger import setup_logger
    setup_logger()

    import argparse

    parser = argparse.ArgumentParser(
        description="Run a hybrid vector + graph query against Neo4j"
    )
    parser.add_argument(
        "--query",
        help="Search query (if omitted, runs interactively)",
    )
    parser.add_argument(
        "--label",
        default="Product",
        help="Node label to search (default: Product)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=config.TOP_K,
        help=f"Number of results (default: {config.TOP_K})",
    )
    parser.add_argument(
        "--index",
        default="vector_index",
        help="Vector index name (default: vector_index)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    args = parser.parse_args()

    query = args.query
    if not query:
        query = input("\n   🔍  Enter your query: ")

    log_phase("4", "Hybrid Query")
    results = hybrid_search(
        user_query=query,
        label=args.label,
        top_k=args.top_k,
        index_name=args.index,
    )

    log_step("Results:")
    indent = 2 if args.pretty else None
    print(json.dumps(results, indent=indent, default=str))


if __name__ == "__main__":
    main()
