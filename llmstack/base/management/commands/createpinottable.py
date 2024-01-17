import requests
from django.core.management.base import BaseCommand
from promptly_pinot_backend.tables import REALTIME_TABLES


class Command(BaseCommand):
    help = "Creates Table in Pinot"

    def add_arguments(self, parser):
        parser.add_argument("table_name", type=str, help="The table name")
        parser.add_argument(
            "controller_url",
            type=str,
            help="Pinot controller url",
        )

    def handle(self, *args, **options):
        name = options["table_name"]
        controller_url = options["controller_url"]
        if name not in REALTIME_TABLES:
            self.stdout.write(self.style.ERROR("Table not found."))

        requests.post(
            controller_url,
            json=REALTIME_TABLES[name],
        )

        self.stdout.write(self.style.SUCCESS("Table created."))
