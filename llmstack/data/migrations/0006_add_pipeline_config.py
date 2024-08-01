# Generated by Django 4.2.11 on 2024-07-24 17:15

from django.db import migrations

PIPELINE_DATA_WITHOUT_SRC = {
    "transformations": [
        {
            "data": {
                "strategy": {
                    "overlap": None,
                    "overlap_all": None,
                    "max_characters": 1000,
                    "new_after_n_chars": None,
                }
            },
            "slug": "splitter",
            "provider_slug": "unstructured",
        }
    ],
    "embedding": {
        "data": {"embedding_provider_slug": "openai"},
        "slug": "embeddings-generator",
        "provider_slug": "promptly",
    },
    "destination": {
        "data": {
            "additional_kwargs": {},
            "store_provider_slug": "weaviate",
            "store_processor_slug": "vector-store",
        },
        "slug": "vector-store",
        "provider_slug": "promptly",
    },
}

SINGLESTORE_PIPELINE_DATA = {
    "source": None,
    "transformations": [],
    "embedding": None,
    "destination": {"slug": "singlestore", "provider_slug": "singlestore", "data": {}},
}


def add_legacy_pipeline_to_datasource_config(apps, schema_editor):
    from llmstack.base.models import Profile
    from llmstack.data.models import DataSource

    datasources = DataSource.objects.all()
    for datasource in datasources:
        pipeline_data = {**PIPELINE_DATA_WITHOUT_SRC}
        type_slug = datasource.config.get("type_slug")
        owner_profile = Profile.objects.get(user=datasource.owner)

        if owner_profile.vectostore_embedding_endpoint == "azure_openai":
            pipeline_data["embedding"]["data"]["embedding_provider_slug"] = "azure-openai"

        if type_slug and type_slug in ["pdf", "text", "url", "file"]:
            # Add src config
            pipeline_data["source"] = {"slug": type_slug, "provider_slug": "promptly", "data": {}}
            # Add index name as Datasource_<uuid> to match legacy schema
            index_name = f"Datasource_{datasource.uuid}".replace("-", "_")
            pipeline_data["destination"]["data"]["additional_kwargs"] = {"index_name": index_name}

        elif type_slug and type_slug == "singlestore":
            pipeline_data = {**SINGLESTORE_PIPELINE_DATA}
        else:
            continue

        datasource_config = {**datasource.config} or {}
        datasource_config["pipeline"] = pipeline_data
        datasource.config = {**datasource_config}
        datasource.save()


class Migration(migrations.Migration):

    dependencies = [
        ("datasources", "0005_populate_type_slug"),
    ]

    operations = [
        migrations.RunPython(add_legacy_pipeline_to_datasource_config, reverse_code=migrations.RunPython.noop),
    ]
