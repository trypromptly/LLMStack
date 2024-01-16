import csv
from io import StringIO
from typing import Any, Dict, List, Optional

import requests
import weaviate
from django.conf import settings
from django.core.management.base import BaseCommand
from pydantic import BaseModel, Field

WEAVIATE_URL = settings.WEAVIATE_URL

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
    help = "Dumps the data from vector store."

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            type=str,
            default="json",
            help="Format of the output file. (json, yaml, pickle) (default: json)",
        )
        parser.add_argument("--output", type=str, default="console")
        parser.add_argument(
            "--filename",
            type=str,
            default="weaviate_data.json",
        )

    def handle(self, *args, **options):
        format = options["format"]
        output = options["output"]
        filename = options["filename"]

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

        if format == "json":
            result = weaviate_schema.json(indent=2)
        else:
            raise Exception("Format not supported.")

        if output == "console":
            self.stdout.write(result)
        elif output == "file":
            with open(filename, "w") as f:
                f.write(result)
        else:
            raise Exception("Output not supported.")
