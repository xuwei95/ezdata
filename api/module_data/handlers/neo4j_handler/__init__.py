"""Neo4j 数据源 handler。"""

from module_data.handlers.neo4j_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.neo4j_handler.neo4j_handler import Neo4jHandler as Handler

version = '0.0.1'
name = 'neo4j'
title = 'Neo4j'
description = 'Neo4j(Cypher,neo4j 驱动 + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
