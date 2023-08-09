import datetime
import io
import json
import logging
from typing import Generic
from typing import Optional

from pydantic import Field
from pydantic import SecretStr
from sqlalchemy import create_engine

from common.promptly.core.base import BaseConfiguration
from common.promptly.core.base import BaseConfigurationType
from common.promptly.core.base import BaseError
from common.promptly.core.base import BaseErrorOutput
from common.promptly.core.base import BaseInput
from common.promptly.core.base import BaseInputType
from common.promptly.core.base import BaseOutput
from common.promptly.core.base import BaseOutputType
from common.promptly.core.base import BaseProcessor
from common.promptly.core.base import CacheManager
from common.utils.text_extract import extract_text_from_b64_json
from common.utils.utils import validate_parse_data_uri

logger = logging.getLogger(__name__)


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


class QueryInput(BaseInput):
    query: str


class QueryOutput(BaseOutput):
    result: Optional[str] = None


class QueryConfiguration(BaseConfiguration):
    pass


class QueryProcessor(BaseProcessor[QueryInput, QueryOutput, QueryConfiguration], Generic[BaseInputType, BaseOutputType, BaseConfigurationType]):
    @staticmethod
    def name() -> str:
        return 'query_processor'

    def schema(self) -> str:
        raise NotImplementedError

    def __init__(self, configuration: dict, cache_manager: CacheManager = None, input_tx_cb: callable = None, output_tx_cb: callable = None):
        super().__init__(configuration, cache_manager, input_tx_cb, output_tx_cb)

    def _process(self, input: QueryInput, configuration: QueryConfiguration) -> QueryOutput:
        pass

    def _process_exception(self, ex: Exception) -> BaseOutputType:
        pass


class SQLQueryProcessor(QueryProcessor[QueryInput, QueryOutput, QueryConfiguration], Generic[BaseInputType, BaseOutputType, BaseConfigurationType]):
    @staticmethod
    def full_table_name(schema, name):
        if '.' in name:
            name = '"{}"'.format(name)

        return '{}.{}'.format(schema, name)

    @staticmethod
    def build_schema(query_result):
        schema = {}
        # By default we omit the public schema name from the table name. But there are
        # edge cases, where this might cause conflicts. For example:
        # * We have a schema named "main" with table "users".
        # * We have a table named "main.users" in the public schema.
        # (while this feels unlikely, this actually happened)
        # In this case if we omit the schema name for the public table, we will have
        # a conflict.
        table_names = set(
            map(
                lambda r: SQLQueryProcessor.full_table_name(
                    r['table_schema'], r['table_name'],
                ),
                query_result,
            ),
        )

        for row in query_result:
            if row['table_schema'] != 'public':
                table_name = SQLQueryProcessor.full_table_name(
                    row['table_schema'], row['table_name'],
                )
            else:
                if row['table_name'] in table_names:
                    table_name = SQLQueryProcessor.full_table_name(
                        row['table_schema'], row['table_name'],
                    )
                else:
                    table_name = row['table_name']

            if table_name not in schema:
                schema[table_name] = {'name': table_name, 'columns': []}

            column = row['column_name']
            if row.get('data_type') is not None:
                column = {
                    'name': row['column_name'],
                    'type': row['data_type'],
                }

            schema[table_name]['columns'].append(column)
        return schema

    def _get_tables(self) -> str:
        raise NotImplementedError

    def schema(self) -> str:
        return self._get_tables()

    @staticmethod
    def name() -> str:
        return 'sql_query_processor'

    def _process(self, input: QueryInput, configuration: QueryConfiguration) -> QueryOutput:
        pass

    def _process_exception(self, ex: Exception) -> BaseOutputType:
        pass


class HTTPQueryProcessor(QueryProcessor[QueryInput, QueryOutput, QueryConfiguration], Generic[BaseInputType, BaseOutputType, BaseConfigurationType]):
    def name(self) -> str:
        return 'http_query_processor'

    def _process(self, input: QueryInput, configuration: QueryConfiguration) -> QueryOutput:
        pass

    def _process_exception(self, ex: Exception) -> BaseOutputType:
        pass


class CSVQueryConfiguration(BaseConfiguration):
    _type = 'csv_query_configuration'
    file: str = Field(
        ..., widget='file',
        description='File to be processed', accepts={
            'text/csv': [],
        },
    )
    csv_delimiter: Optional[str] = ','


class CSVQueryProcessor(QueryProcessor[QueryInput, QueryOutput, CSVQueryConfiguration], Generic[BaseInputType, BaseOutputType, BaseConfigurationType]):

    def __init__(self, configuration: dict, cache_manager: CacheManager = None, input_tx_cb: callable = None, output_tx_cb: callable = None):

        super().__init__(configuration, cache_manager, input_tx_cb, output_tx_cb)
        self.csv_data = None

    def name(self) -> str:
        return 'csv_query_processor'

    def schema(self) -> str:
        return self.process(QueryInput(query='schema'))

    def _process(self, input: QueryInput, configuration: CSVQueryConfiguration) -> QueryOutput:
        import pandas as pd
        import numpy as np

        if self.csv_data is None:
            mime_type, file_name, data = validate_parse_data_uri(
                configuration.file,
            )
            csv_file_data = extract_text_from_b64_json(
                'text/csv', data,
            )

            workbook = pd.read_csv(
                io.StringIO(csv_file_data),
                sep=self._config.csv_delimiter,
            )
            df = workbook.copy()
            conversions = [
                {'pandas_type': np.integer, 'type': 'integer'},
                {'pandas_type': np.inexact, 'type': 'float'},
                {'pandas_type': np.datetime64, 'type': 'datetime'},
                {'pandas_type': np.bool_, 'type': 'boolean'},
                {'pandas_type': np.object, 'type': 'string'},
            ]
            labels = []
            data = {'columns': [], 'rows': []}

            for dtype, label in zip(df.dtypes, df.columns):
                for conversion in conversions:
                    if issubclass(dtype.type, conversion['pandas_type']):
                        data['columns'].append(
                            {'name': label, 'type': conversion['type']},
                        )
                        labels.append(label)
                        break
            data['rows'] = df[labels].replace(
                {np.nan: None},
            ).to_dict(orient='records')
            self.csv_data = data

        if input.query == 'schema':
            return [{'name': file_name, 'columns': self.csv_data['columns']}]
        else:
            return QueryOutput(result=json.dumps(self.csv_data['rows']))

    def _process_exception(self, ex: Exception) -> BaseOutputType:
        pass


class PostgresQueryConfiguration(QueryConfiguration):
    _type = 'postgres_query_configuration'
    user: Optional[str] = Field(..., description='Postgres user')
    password: Optional[SecretStr] = Field(..., description='Postgres password')
    host: Optional[str] = Field(..., description='Postgres host')
    port: Optional[int] = Field(..., description='Postgres port')
    dbname: Optional[str] = Field(..., description='Postgres database name')


class PostgresQueryProcessor(SQLQueryProcessor[QueryInput, QueryOutput, PostgresQueryConfiguration], Generic[BaseInputType, BaseOutputType, BaseConfigurationType]):
    def name(self) -> str:
        return 'postgres_query_processor'

    def _get_tables(self) -> str:
        query = """
        SELECT s.nspname as table_schema,
               c.relname as table_name,
               a.attname as column_name,
               null as data_type
        FROM pg_class c
        JOIN pg_namespace s
        ON c.relnamespace = s.oid
        AND s.nspname NOT IN ('pg_catalog', 'information_schema')
        JOIN pg_attribute a
        ON a.attrelid = c.oid
        AND a.attnum > 0
        AND NOT a.attisdropped
        WHERE c.relkind IN ('m', 'f', 'p')
        UNION
        SELECT table_schema,
               table_name,
               column_name,
               data_type
        FROM information_schema.columns
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        """
        result = self.process(QueryInput(query=query).dict())
        if isinstance(result, QueryOutput):
            return list(SQLQueryProcessor.build_schema(json.loads(result.result)).values())
        else:
            raise Exception('Error getting tables information')

    def _process(self, input: QueryInput, configuration: PostgresQueryConfiguration) -> QueryOutput:
        postgres_url = 'postgresql://%s:%s@%s:%s/%s' % (
            configuration.user, configuration.password.get_secret_value(), configuration.host, configuration.port, configuration.dbname,
        )

        engine = create_engine(postgres_url)
        # execute the query and fetch the results
        with engine.connect() as connection:
            result = connection.execute(input.query)
            rows = result.fetchall()

        return QueryOutput(result=json.dumps([dict(row) for row in rows], default=default))

    def _process_exception(self, ex: Exception) -> BaseOutputType:
        return BaseErrorOutput(error=BaseError(message=str(ex), code=-1))


class BigQueryQueryConfiguration(QueryConfiguration):
    _type = 'bigquery_query_configuration'
    project_id: str = Field(..., description='BigQuery project id')
    credentials: SecretStr = Field(..., description='BigQuery credentials')
    location: str = Field(description='BigQuery location', default='US')


# class BiqQueryProcessor(SQLQueryProcessor[QueryInput, QueryOutput, PostgresQueryConfiguration], Generic[BaseInputType, BaseOutputType, BaseConfigurationType]):
#     def name(self) -> str:
#         return "bigquery_query_processor"

#     def _process(self, input: QueryInput, configuration: PostgresQueryConfiguration) -> QueryOutput:

#         client = bigquery.Client(
#             configuration.credentials.get_secret_value())
#         query_job = client.query(
#             input.query, location=self._config.location)

#         rows = query_job.result()

#         return QueryOutput(result=json.dumps(rows))

#     def _process_exception(self, ex: Exception) -> BaseOutputType:
#         pass


class MySQLQueryConfiguration(QueryConfiguration):
    _type = 'mysql_query_configuration'
    user: Optional[str] = Field(..., description='Postgres user')
    password: Optional[SecretStr] = Field(..., description='Postgres password')
    host: Optional[str] = Field(..., description='Postgres host')
    port: Optional[int] = Field(..., description='Postgres port')
    dbname: Optional[str] = Field(..., description='Postgres database name')


class MySQLQueryProcessor(SQLQueryProcessor[QueryInput, QueryOutput, MySQLQueryConfiguration], Generic[BaseInputType, BaseOutputType, BaseConfigurationType]):
    def name(self) -> str:
        return 'mysql_query_processor'

    def _process(self, input: QueryInput, configuration: MySQLQueryConfiguration) -> QueryOutput:
        mysql_url = 'mysql://%s:%s@%s:%s/%s' % (
            configuration.user, configuration.password.get_secret_value(), configuration.host, configuration.port, configuration.dbname,
        )
        engine = create_engine(mysql_url)
        # execute the query and fetch the results
        with engine.connect() as connection:
            result = connection.execute(input.query)
            rows = result.fetchall()
            logger.error(rows)

        return QueryOutput(result=json.dumps([dict(row) for row in rows], default=default))

    def _process_exception(self, ex: Exception) -> BaseOutputType:
        return BaseErrorOutput(error=BaseError(message=str(ex), code=-1))
