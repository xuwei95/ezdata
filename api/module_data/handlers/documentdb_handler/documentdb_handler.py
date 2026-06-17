"""DocumentDB handler:MongoDB 兼容,直接继承 MongoDBHandler。"""

from module_data.handlers.documentdb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.mongodb_handler.mongodb_handler import MongoDBHandler


class DocumentDBHandler(MongoDBHandler):
    name = 'documentdb'
    title = 'Amazon DocumentDB'
    connection_args = connection_args
    connection_args_example = connection_args_example
