from django.db import models
import json


class ArrayField(models.TextField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return []
        return json.loads(value)

    def to_python(self, value):
        if isinstance(value, list):
            return value
        if value is None:
            return []
        return json.loads(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if value is None:
            return None
        return json.dumps(value)
