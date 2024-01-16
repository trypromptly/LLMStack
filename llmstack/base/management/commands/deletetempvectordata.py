import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import weaviate
from django.conf import settings
from django.core.management.base import BaseCommand
from pydantic import BaseModel, Field

WEAVIATE_URL = settings.WEAVIATE_URL
DEFAULT_TIME_CUTOFF_MINS = 24 * 60

client = weaviate.Client(WEAVIATE_URL)


class WeaviateClassObject(BaseModel):
    className: str = Field(..., alias="class")
    creationTimeUnix: int = Field(..., alias="creationTimeUnix")
    id: str = Field(..., alias="id")
    lastUpdateTimeUnix: int = Field(..., alias="lastUpdateTimeUnix")
    properties: Dict[str, Any]
    vectorWeights: Optional[Dict[str, Any]] = None
    vector: Optional[List[Any]]


class WeaviateClass(BaseModel):
    className: str = Field(..., alias="class")
    description: Optional[str] = None
    invertedIndexConfig: Optional[Dict] = None
    moduleConfig: Optional[Dict] = None
    properties: Optional[List[Any]] = None
    replicationConfig: Optional[Dict] = None
    shardingConfig: Optional[Dict] = None
    vectorIndexConfig: Optional[Dict] = None
    vectorIndexType: Optional[str] = None
    vectorizer: Optional[str] = None
    objects: Optional[List[WeaviateClassObject]] = None


class WeaviateSchema(BaseModel):
    classes: List[WeaviateClass]


def get_schema():
    url = f"{WEAVIATE_URL}/v1/schema"
    return requests.get(url).json()


def get_objects(class_name, limit=1000, last_document_id=None):
    if last_document_id:
        url = f"{WEAVIATE_URL}/v1/objects/?class={class_name}&limit={limit}&after={last_document_id}&include=classification,vector"
    else:
        url = f"{WEAVIATE_URL}/v1/objects/?class={class_name}&limit={limit}&include=classification,vector"
    result = requests.get(url).json()
    if len(result["objects"]) > 0:
        last_document_id = result["objects"][-1]["id"]
        result["objects"] += get_objects(class_name, limit, last_document_id)
    return result["objects"]


def get_class(class_name):
    return get_objects(class_name)


class Command(BaseCommand):
    help = "Delete temp data from vector store."

    def add_arguments(self, parser):
        parser.add_argument(
            "--not-dry-run",
            action="store_true",
            help="Do not perform any actions, just print what would be done.",
        )

        parser.add_argument(
            "--duration",
            type=str,
            default="7 days",
            help='Specify the duration in the format "X days" or "Y mins".',
        )

    def parse_duration(self, duration_str):
        # Use regular expressions to parse the input duration string
        match = re.match(
            r"^(\d+)\s*(days?|mins?)$",
            duration_str,
            re.IGNORECASE,
        )
        if not match:
            raise ValueError(
                'Invalid duration format. Use "X days" or "Y mins".',
            )

        value, unit = match.groups()
        value = int(value)
        if unit.lower() == "mins":
            return value * 60  # Convert minutes to seconds
        elif unit.lower() == "days":
            return value * 86400  # Convert days to seconds

    def handle(self, *args, **options):
        dry_run = not options["not_dry_run"]
        duration_str = options.get("duration", "")

        if dry_run:
            self.stdout.write("Running in dry-run mode.")

        if duration_str:
            try:
                duration_seconds = self.parse_duration(duration_str)
                duration_minutes = int(duration_seconds / 60)
                self.stdout.write(f"Duration: {duration_minutes} minutes.")
            except ValueError as e:
                self.stderr.write(str(e))
                return

        now = int(datetime.utcnow().timestamp()) * 1000
        weaviate_schema = WeaviateSchema(**get_schema())
        for wclass in weaviate_schema.classes:
            objects = list(
                map(
                    lambda x: WeaviateClassObject(
                        **x,
                    ),
                    get_class(wclass.className),
                ),
            )
            wclass.objects = objects

        for wclass in weaviate_schema.classes:
            if wclass.className.startswith("Temp_"):
                lastUpdateTimestamps = []
                object_ids = []
                for object in wclass.objects:
                    # add delta in minutes
                    object_ids.append(object.id)
                    lastUpdateTimestamps.append(
                        int((now - object.lastUpdateTimeUnix) / 1000 / 60),
                    )
                lastUpdateTimestamps.sort()
                if (
                    len(
                        lastUpdateTimestamps,
                    )
                    > 0
                    and lastUpdateTimestamps[0] > duration_minutes
                ):
                    self.stdout.write(f"Deleting {wclass.className}...")
                    self.stdout.write(
                        f'Deleting Objects {" ".join(object_ids)}..."',
                    )
                    result = client.batch.delete_objects(
                        class_name=wclass.className,
                        where={
                            "path": ["source"],
                            "operator": "Like",
                            "valueString": "*",
                        },
                        dry_run=dry_run,
                    )
                    self.stdout.write(json.dumps(result, indent=2))
