---
id: add-custom-processor
title: Add Custom Processor
---

A processor is the smallest building block in LLMStack. It is a function that takes some input, does something with it, and returns some output. Each processor defines its own input, configuration, and output schemas.

Adding a new processor is easy. You can add a new processor by creating a new module in `llmstack/processors/providers/` directory and adding a processor implementation under `llmstack/processors/providers/<provider-name>`. You can check out the `Echo Processor` [implementation](https://github.com/trypromptly/LLMStack/blob/main/llmstack/processors/providers/promptly/echo.py) for reference.

```bash
cd llmstack/processors/providers
mkdir <provider-name>
cd <provider-name>
touch __init__.py
touch sample.py
```

### Define Input, Configuration, and Output Schemas

You start by defining the input, configuration, and output schemas for your processor. You can define the schemas in the `sample.py` file. We use pydatic `BaseModel` for schema definitions. You can check out the [pydantic documentation](https://docs.pydantic.dev/latest/concepts/models/) for more information.

Each schema model should inherit from `ApiProcessorSchema` and define the fields. Check pydantic documentation for more information on [defining fields](https://docs.pydantic.dev/latest/concepts/models/#nested-models).

```python
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

class SampleInput(ApiProcessorSchema):
    prompt: str
    search_filters: str

class SampleConfiguration(ApiProcessorSchema):
    model: str

class SampleOutput(ApiProcessorSchema):
    answer: str
```

:::note
Use `<processor-name>Input`, `<processor-name>Configuration`, and `<processor-name>Output` as the class names for input, configuration, and output schemas respectively.

Fields that you expect to change for each input request should be defined in the input schema.
:::

### Define Processor Implementation

Once we have the schemas defined, we can start with the processor implementation. Each processor implmentation should inherit from `ApiProcessorInterface`.

```python

class SampleProcessor(ApiProcessorInterface[SampleInput, SampleOutput, SampleConfiguration])
```

Each processor implementation should define the following methods:

#### `name()`

This is the display name of the processor. This is used in the UI to display the processor name.

```python
@staticmethod
 def name() -> str:
    return 'Sample'
```

#### `slug()`

This is the slug of the processor.
:::note
This should be unique across all processors.
:::

```python
@staticmethod
def slug() -> str:
    return 'sample'
```

#### `description()`

This is the description of the processor. This is used in the UI to display the processor description.

```python
@staticmethod
def description() -> str:
    return 'Echoes the input string'
```

#### `provider_slug()`

This is the slug of the provider. This will be used in the UI to group your processor under the provider.

```python
@staticmethod
def provider_slug() -> str:
    return 'acme'
```

#### `process()`

This is the main method of the processor. This is where you define the logic for your processor. The llmstack framework will call this method when the processor is invoked.

You can access the input and configuration specified by the user using `self._input` and `self._configuration` respectively.

The llmstack framework supports streaming output out-of-the-box. You can stream your output by continuously calling `self._output_stream.write` method. You are only responsible for writing the delta output. The llmstack framework will take care of the rest.

You can return the final output by calling `self._output_stream.finalize()` method.
:::note
Don't forget to call `finalize()` method at the end of your `process()` method.
:::

##### Non-streaming Example:

In the below example the output is not streamed. The user will see the entire output at once.

```python
def process(self):
    output_stream = self._output_stream
    async_to_sync(output_stream.write)(
        SampleOutput(answer="Hello World")
    )
    output = output_stream.finalize()
    return output
```

##### Streaming Example:

In the below example we stream the each character in the string "Hello World" with a delay of 1 second. The user will see the output being streamed in real-time (1 character/second).

```python
def process(self):
    output_stream = self._output_stream
    for i in "Hello World":
        async_to_sync(output_stream.write)(SampleOutput(answer=i))
        time.sleep(1)
    output = output_stream.finalize()
    return output
```
