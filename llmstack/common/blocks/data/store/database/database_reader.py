import collections
import datetime
import json
import uuid

import sqlalchemy
from psycopg2.extras import Range

from llmstack.common.blocks.base.processor import ProcessorInterface
from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.common.blocks.data import DataDocument
from llmstack.common.blocks.data.store.database.utils import (
    DatabaseConfiguration,
    DatabaseOutput,
    get_database_connection,
)


class DatabaseJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Range):
            # From: https://github.com/psycopg/psycopg2/pull/779
            if o._bounds is None:
                return ""

            items = [
                o._bounds[0],
                str(
                    o._lower,
                ),
                ", ",
                str(
                    o._upper,
                ),
                o._bounds[1],
            ]

            return "".join(items)
        elif isinstance(o, uuid.UUID):
            return str(o.hex)
        elif isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

        return super().default(o)


class DatabaseReaderInput(BaseSchema):
    sql: str


class DatabaseReader(
    ProcessorInterface[DatabaseReaderInput, DatabaseOutput, DatabaseConfiguration],
):
    def fetch_columns(self, columns):
        column_names = set()
        duplicates_counters = collections.defaultdict(int)
        new_columns = []

        for col in columns:
            column_name = col[0]
            while column_name in column_names:
                duplicates_counters[col[0]] += 1
                column_name = "{}{}".format(
                    col[0],
                    duplicates_counters[col[0]],
                )

            column_names.add(column_name)
            new_columns.append({"name": column_name, "type": col[1]})

        return new_columns

    def process(
        self,
        input: DatabaseReaderInput,
        configuration: DatabaseConfiguration,
    ) -> DatabaseOutput:
        connection = get_database_connection(configuration=configuration)
        try:
            result = connection.execute(sqlalchemy.text(input.sql))
            cursor = result.cursor

            if cursor.description is not None:
                columns = self.fetch_columns(
                    [(i[0], None) for i in cursor.description],
                )
                rows = [dict(zip((column["name"] for column in columns), row)) for row in cursor]

                data = {"columns": columns, "rows": rows}
                json_data = json.dumps(data, cls=DatabaseJSONEncoder)
            else:
                raise Exception("Query completed but it returned no data.")
        except Exception as e:
            connection.close()
            connection.engine.dispose()
            raise e
        return DatabaseOutput(
            documents=[
                DataDocument(
                    content=json_data,
                    content_text=json_data,
                    metadata={
                        "mime_type": "application/json",
                    },
                ),
            ],
        )
