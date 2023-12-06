---
id: add-external-datasource
title: Add External Datasource
---

LLMStack supports adding an external datastore as a read-only datasource. Adding an external datastore gives you the ability to query the datastore and use the results in your LLM applications.

Adding an external datasource is easy. Add a new module in `llmstack/datasources/handlers/databases/` add your implmentation as `<datasource-name>.py`. You can check out the `Postgres Datasource` [implementation](https://github.com/trypromptly/LLMStack/blob/main/llmstack/datasources/handlers/databases/postgres.py)

```bash
cd llmstack/datasources/handlers/databases
touch <datasource-name>.py
```

### Define Database Handler Connection Schema

You start by defining the database connection schema. You can define the schemas in the `<datasource-name>.py` file. We use pydatic for schema definitions. So make sure your schema definition class inherits from `llmstack.datasources.handlers.datasource_processor import DataSourceSchema`.

In case of our example Postgres Implementation, we define the connection schema as follows:

```python
from llmstack.common.blocks.base.schema import BaseSchema
class PostgresConnection(BaseSchema):
    host: str = Field(description='Host of the Postgres instance')
    port: int = Field(
        description='Port number to connect to the Postgres instance')
    database_name: str = Field(description='Postgres database name')
    username: str = Field(description='Postgres username')
    password: Optional[str] = Field(description='Postgres password')


class PostgresDatabaseSchema(DataSourceSchema):
    connection: Optional[PostgresConnection] = Field(
        description='Postgres connection details')
```

**llmstack** framework takes care of storing the connection details in the database in an encrypted format or as plain text. To define this behavior you will also need to define a `ConnectionConfiguration` class. This class will inherit from `from llmstack.common.utils.models import Config`.
e.g

```python
class PostgresConnectionConfiguration(Config):
    config_type = 'postgres_connection'
    is_encrypted = True
    postgres_config: Optional[Dict]
```

The database connection details will be stored in the `postgres_config` key and will be encrypted if `is_encrypted` is set to `True`.

:::note
Defining this class is mandatory regardless of whether you want to store the connection details as encrypted or not.
:::

### Define Database Handler Implementation

Once we have the schemas defined, we can start with the database handler implementation. Each database handler implmentation should inherit from `llmstack.datasources.handlers.datasource_processor.DataSourceProcessor`. Each implementation needs to implement the following methods:

#### `def __init__(datasource: DataSource))` :

The constructor will be passed the `DataSource` object. You can use the datasource object to access the database related configuration. The configuration will be available in the `data` key of the `datasource.config` object.
You can access the database connection object as follows:

```python
config_dict = PostgresConnectionConfiguration().from_dict(
                self.datasource.config, self.datasource.profile.decrypt_value)
self._postgres_database_schema = PostgresDatabaseSchema(
                **config_dict['postgres_config'])

```

You can intialize you class as required from the connection dictionary as passed above.

#### `def name()` :

Define a name for your implementation. This name will be used to identify the datasource connection type. This will be displayed in the UI.

#### `def slug()` :

Define a slug for your implementation. This slug will be used to identify the datasource connection type.

#### `def description()` :

Provide a helpful description for your implementation. This will be displayed in the UI.

#### `def provider_slug()`

Provide a vendor slug for your database. Make sure this is unique, you can use the database provider/company name here.

#### `def process_validate_config()` :

When a user tries to add an external database, this method will be called with the details that the user provides. You can use this method to validate the connection details provided by the user. You can raise an exception if the connection details are invalid. Make sure this method returns a instance of your `ConnectionConfiguration` class.

#### `def similarity_search()`

Depending on your underlying database, you can implement a similarity search method. This method will be called when a user tries to search for a record in the database. You can use this method to search for similar records in the database and return the results.

#### `def hybrid_search()`

Depending on your underlying database, you can implement a hybrid search method. This method will be called when a user tries to search for a record in the database. You can use this method to search for similar records in the database and return the results.

:::note
If your underlying database does not support similarity search or hybrid search, you can simple implement a single `search` method and call that from both the `similarity_search` and `hybrid_search` methods. Implementing both the methods is required. The methods will be passed in the search query that user has entered. The methods should return a list of `Document` objects.
e.g `[Document(page_content_key='content', page_content=str(<database-records>), metadata={'score': 0, 'source': self._source_name})]`
Here `page_content` will contain you records retrieved from the datbase. This can be list of csv values or a json object serialized as string.
:::
