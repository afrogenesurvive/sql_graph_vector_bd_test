"""Database connection factories for Neo4j and MySQL."""

import pymysql
from neo4j import GraphDatabase
from neo4j import Driver as Neo4jDriver

from scripts import config


def get_neo4j_driver() -> Neo4jDriver:
    """Return a Neo4j driver instance."""
    return GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
    )


def get_mysql_connection() -> pymysql.Connection:
    """Return a PyMySQL connection using environment config."""
    return pymysql.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
