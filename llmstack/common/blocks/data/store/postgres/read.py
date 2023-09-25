from collections import defaultdict
import json
from llmstack.common.blocks.base.processor import ProcessorInterface
from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.common.blocks.data import DataDocument
from llmstack.common.blocks.data.store.postgres import PostgresConfiguration, PostgresOutput, get_pg_connection
from psycopg2.extras import Range

class PostgresReaderInput(BaseSchema):
    sql: str

types_map = {
    20: "integer",
    21: "integer",
    23:  "integer",
    700: "float",
    1700: "float",
    701: "float",
    16: "boolean",
    1082: "date",
    1182: "date",
    1114: "datetime",
    1184: "datetime",
    1115: "datetime",
    1185: "datetime",
    1014: "string",
    1015: "string",
    1008: "string",
    1009: "string",
    2951: "string",
    1043: "string",
    1002: "string",
    1003: "string",
}

class PostgreSQLJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Range):
            # From: https://github.com/psycopg/psycopg2/pull/779
            if o._bounds is None:
                return ""

            items = [o._bounds[0], str(o._lower), ", ", str(o._upper), o._bounds[1]]

            return "".join(items)

        return super(PostgreSQLJSONEncoder, self).default(o)
    
class PostgresReader(ProcessorInterface[PostgresReaderInput, PostgresOutput, PostgresConfiguration]):
    def fetch_columns(self, columns):
        column_names = set()
        duplicates_counters = defaultdict(int)
        new_columns = []

        for col in columns:
            column_name = col[0]
            while column_name in column_names:
                duplicates_counters[col[0]] += 1
                column_name = "{}{}".format(col[0], duplicates_counters[col[0]])

            column_names.add(column_name)
            new_columns.append({"name": column_name, "friendly_name": column_name, "type": col[1]})

        return new_columns
    
    def process(self, input: PostgresReaderInput, configuration: PostgresConfiguration) -> PostgresOutput:
        connection = get_pg_connection(configuration.dict())
        cursor = connection.cursor()
        try:
            cursor.execute(input.sql)
            if cursor.description is not None:
                columns = self.fetch_columns([(i[0], types_map.get(i[1], None)) for i in cursor.description])
                rows = [dict(zip((column["name"] for column in columns), row)) for row in cursor]

                data = {"columns": columns, "rows": rows}
                json_data = json.dumps(data, cls=PostgreSQLJSONEncoder)
            else:
                raise Exception("Query completed but it returned no data.")
        except Exception as e:
            connection.cancel()
            raise e 
        return PostgresOutput(documents=[DataDocument(content=json_data, content_text=json_data, metadata={"mime_type": "application/json"})])