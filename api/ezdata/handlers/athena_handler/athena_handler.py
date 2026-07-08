"""Amazon Athena handler:SqlConnector + PyAthena(aws 凭据 + region + S3 staging dir)。"""

from urllib.parse import quote_plus, urlencode

from ezdata.handlers.athena_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class AthenaHandler(SqlConnector):
    name = 'athena'
    title = 'Amazon Athena'
    driver = 'awsathena+rest'
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        ak = quote_plus(str(self.arg('aws_access_key_id', default='')))
        sk = quote_plus(str(self.arg('aws_secret_access_key', default='')))
        region = self.arg('region_name', default='us-east-1')
        database = self.arg('database', default='default')
        params = {
            k: v
            for k, v in {
                's3_staging_dir': self.arg('results_output_location'),
                'work_group': self.arg('workgroup'),
                'catalog_name': self.arg('catalog'),
            }.items()
            if v
        }
        qs = f'?{urlencode(params)}' if params else ''
        return f'awsathena+rest://{ak}:{sk}@athena.{region}.amazonaws.com:443/{database}{qs}'
