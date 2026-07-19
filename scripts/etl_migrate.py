"""Phase 2: MySQL → Neo4j ETL Migration.

Discovers tables via ``information_schema``, migrates each table to Neo4j
nodes, then creates relationships based on foreign keys.
"""

from typing import Dict, List, Optional

import pymysql

from scripts import config
from scripts.db import get_neo4j_driver, get_mysql_connection
from scripts.logger import get_logger, log_ok, log_step, log_warn, log_phase

logger = get_logger(__name__)


# ── Table discovery ──────────────────────────────────────


def discover_tables(cursor: pymysql.cursors.DictCursor) -> List[str]:
    """Return a list of user table names in the configured database."""
    cursor.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = %s AND table_type = 'BASE TABLE'",
        (config.MYSQL_DATABASE,),
    )
    return [row["table_name"] for row in cursor.fetchall()]


def discover_foreign_keys(cursor: pymysql.cursors.DictCursor) -> List[Dict]:
    """Return foreign-key metadata for the configured database."""
    cursor.execute(
        """
        SELECT
            kcu.table_name              AS child_table,
            kcu.column_name             AS child_column,
            kcu.referenced_table_name   AS parent_table,
            kcu.referenced_column_name  AS parent_column
        FROM information_schema.key_column_usage kcu
        WHERE kcu.table_schema = %s
          AND kcu.referenced_table_name IS NOT NULL
        ORDER BY kcu.table_name, kcu.ordinal_position
        """,
        (config.MYSQL_DATABASE,),
    )
    return cursor.fetchall()  # type: ignore[return-value]


# ── Migration helpers ────────────────────────────────────


def _table_label(table_name: str) -> str:
    """Convert a SQL table name to a Neo4j label (singular, title-case)."""
    # Special-case known plurals
    overrides = {
        "products": "Product",
        "customers": "Customer",
        "orders": "Order",
        "order_items": "OrderItem",
    }
    return overrides.get(table_name, table_name.title())


def migrate_table(
    table_name: str,
    label: Optional[str] = None,
    limit: int = 1000,
) -> int:
    """Migrate rows from *table_name* to Neo4j nodes with label *label*.

    Returns the number of rows migrated.
    """
    label = label or _table_label(table_name)
    mysql = get_mysql_connection()
    neo4j = get_neo4j_driver()
    count = 0

    try:
        with mysql.cursor() as cursor:
            cursor.execute(f"SELECT * FROM `{table_name}` LIMIT %s", (limit,))
            columns = [desc[0] for desc in cursor.description]

            with neo4j.session() as session:
                for row in cursor.fetchall():
                    props = dict(row)  # row is a DictCursor row
                    node_id = props.pop("id", None)

                    # Remove columns that shouldn't be node properties
                    props.pop("created_at", None)

                    if node_id is not None:
                        session.run(
                            f"MERGE (n:{label} {{id: $id}}) SET n += $props",
                            id=node_id,
                            props=props,
                        )
                    else:
                        session.run(
                            f"CREATE (n:{label}) SET n = $props",
                            props=props,
                        )
                    count += 1
    finally:
        mysql.close()
        neo4j.close()

    log_ok(f"Migrated {count} rows → :{label}")
    return count


def migrate_relationships() -> int:
    """Create Neo4j relationships from MySQL foreign keys.

    Returns the number of relationship types created.
    """
    mysql = get_mysql_connection()
    neo4j = get_neo4j_driver()
    rel_count = 0

    try:
        with mysql.cursor() as cursor:
            fks = discover_foreign_keys(cursor)

        with neo4j.session() as session:
            for fk in fks:
                child_label = _table_label(fk["child_table"])
                parent_label = _table_label(fk["parent_table"])
                rel_type = f"BELONGS_TO_{parent_label.upper()}"

                # Remove the trailing _id suffix for a cleaner relationship
                # e.g. customer_id → customer on the child side
                child_attr = fk["child_column"]
                parent_attr = fk["parent_column"]

                logger.info(
                    "Creating :%s -[:%s]-> :%s  (%s → %s)",
                    child_label,
                    rel_type,
                    parent_label,
                    child_attr,
                    parent_attr,
                )

                log_step(
                    f"Linking :{child_label} -[:{rel_type}]-> :{parent_label}"
                )

                session.run(
                    f"""
                    MATCH (child:{child_label})
                    MATCH (parent:{parent_label} {{id: $parent_id}})
                    MERGE (child)-[:`{rel_type}`]->(parent)
                    """,
                    parent_id=fk["child_column"],
                )
                rel_count += 1
    finally:
        mysql.close()
        neo4j.close()

    log_ok(f"Created {rel_count} relationship types")
    return rel_count


# ── CLI ──────────────────────────────────────────────────


def main():
    from scripts.logger import setup_logger
    setup_logger()

    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate MySQL database to Neo4j"
    )
    parser.add_argument(
        "--tables",
        nargs="*",
        help="Specific tables to migrate (default: all user tables)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Max rows per table (default: 1000)",
    )
    parser.add_argument(
        "--skip-relationships",
        action="store_true",
        help="Skip foreign-key relationship creation",
    )
    args = parser.parse_args()

    log_phase("2", "ETL Migration")

    mysql = get_mysql_connection()
    try:
        with mysql.cursor() as cursor:
            if args.tables:
                tables = args.tables
            else:
                log_step("Discovering tables from MySQL...")
                tables = discover_tables(cursor)

            if not tables:
                log_warn(f"No tables found in database '{config.MYSQL_DATABASE}'")
                return

            log_ok(f"{len(tables)} tables found: {', '.join(tables)}")

        for table in tables:
            log_step(f"Migrating table '{table}'...")
            migrate_table(table, limit=args.limit)

        if not args.skip_relationships:
            log_step("Creating foreign-key relationships...")
            migrate_relationships()
    finally:
        mysql.close()

    log_ok("Migration complete.")


if __name__ == "__main__":
    main()
