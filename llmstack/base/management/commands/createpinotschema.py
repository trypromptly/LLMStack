import requests
from django.core.management.base import BaseCommand
from promptly_pinot_backend.tables import SCHEMAS


class Command(BaseCommand):
    help = "Creates Schema in Pinot"

    def add_arguments(self, parser):
        parser.add_argument("schema_name", type=str, help="The table name")
        parser.add_argument(
            "controller_url",
            type=str,
            help="Pinot controller url",
        )

    def handle(self, *args, **options):
        name = options["schema_name"]
        controller_url = options["controller_url"]
        if name not in SCHEMAS:
            self.stdout.write(self.style.ERROR("Schema not found."))

        requests.post(
            controller_url,
            json=SCHEMAS[name],
        )

        self.stdout.write(self.style.SUCCESS("Schema created."))
