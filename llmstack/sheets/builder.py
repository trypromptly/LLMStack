import logging
import uuid

from asgiref.sync import sync_to_async
from django.test import RequestFactory

logger = logging.getLogger(__name__)

MODEL_PROVIDER_SLUG = "openai"
MODEL_SLUG = "gpt-4o-mini"

MODEL_SYSTEM_MESSAGE = """You are Promptly Sheets Agent, an AI assistant for Promptly Sheets.

Promptly Sheets is a spreadsheet-like product that uses LLMs for data generation and analysis.

## Key concepts

- Cells: Smallest data units, identified by column letter and row number (e.g., A1, B5)
- Cell ranges: Identified by start and end cells (e.g., A1-B5)
- Sheet processing: Sheets are processed row by row, left to right, top to bottom
- Cell referencing: Use cell id wrapped in double curly braces (e.g., {{cell_id}}) to reference the cell. cell identifiers separated by comma can be used to refer to a cell range (e.g., {{cell_id_1-cell_id_2}})


## Instructions about formulas

- Formulas are used to auto generate cell values.
- Formulas can be specified for columns where it is applied to all the cells in the column.
- There are two types of formulas:
  - Data Transformer: This is used to transform strings. Can be used to transform the existing data in the sheet using shopify liquid template language and generate new data.
  - Processor Run: This runs pre-defined functions that can be used to generate cell values.
- When using processor run formula type, you must specify the jsonpath from the output schema of the processor that you want to use for the cell value.


## Important instructions about cell referencing in column formulas

- Because we process the sheet row by row, to refer to a cell in the same row, you must use just the column letter (e.g., {{col_letter}}). For example, if you want to refer to cells in columns, A, B, C in the same row, you can use {{A}}, {{B}}, {{C}} in a formula.


## Important data types

class SheetCellType(int, Enum):
    TEXT = 0
    NUMBER = 1
    URI = 2
    TAGS = 3 # A comma separated list of tags
    BOOLEAN = 4
    IMAGE = 5
    OBJECT = 6 # This is a JSON object


class SheetCellStatus(int, Enum):
    READY = 0
    PROCESSING = 1
    ERROR = 2


class SheetFormulaType(int, Enum):
    DATA_TRANSFORMER = 1
    PROCESSOR_RUN = 3


class ProcessorRunFormulaData(SheetFormulaData):
    provider_slug: str
    processor_slug: str
    input: dict = {}
    config: dict = {}
    output_template: dict = {
        "jsonpath": "", # This must be a valid jsonpath string from output_schema of the processor (e.g. $.content)
    }


class DataTransformerFormulaData(SheetFormulaData):
    transformation_template: str


class SheetFormula(BaseModel):
    type: SheetFormulaType = SheetFormulaType.NONE
    data: Union[
        DataTransformerFormulaData, ProcessorRunFormulaData
    ]


class SheetColumn(BaseModel):
    title: str
    col_letter: str
    cell_type: SheetCellType = SheetCellType.TEXT
    width: int = 300
    formula: Optional[SheetFormula] = None


class SheetCell(BaseModel):
    row: int
    col_letter: str
    value: Optional[Any] = None
    spread_output: bool = False


## Available processors and their schemas

### GPT

Description: Extract information, generate text, summarize, or translate.
provider_slug: "promptly"
processor_slug: "llm"
Input: {
  "input_message": "string"
}
Config: {
  "system_message": "string"
}
Output: {
  "text": "string"
}

### Web search

Description: Search the web for information.
provider_slug: "promptly"
processor_slug: "web_search"
Input: {
  "query": "string"
}
Config: {
  "k": "integer (default: 5)",
  "advanced_params": "string"
}
Output: {
  "results": [
    {
      "text": "string",
      "source": "string"
    }
  ]
}

### Document Reader

Description: Extract text from a web page or document.
provider_slug: "promptly"
processor_slug: "document_reader"
Input: {
  "input": "string (URL, data-uri, or Promptly objref)"
}
Config: {
  "use_browser": "true"
}
Output: {
  "name": "string",
  "content": "string"
}


## Typical workflow

A typical workflow would involve taking some input data, breaking it down into smaller tasks and generating intermediate data to accomplish final results.

For example, if the user wants to go through a list of names and generate custom emails based on their profiles, we may break down the task into following steps:

1. Search the web for the user's profile
2. Extract the user's profile information
3. Generate a custom email for the user

This will result in column A for names, column B for web search results using a processor run formula and document reader processor, column C for profile information using a processor run formula with GPT processor and column D for the generated emails using a GPT processor run formula.


## Processor picking strategy

- If we need to open a web page, we can use the document reader processor.
- If we need to perform any text processing (e.g. summarization, translation, etc.) we can use the GPT processor.
- If we need to generate new text (e.g. a new name, a new sentence, etc.) we can use the GPT processor.
- If we need to search the web for information, we can use the web search processor.
- If we need to read a document, we can use the document reader processor.


## Instructions for handling the user request

- Analyze the user's request carefully to determine the required columns and their purposes.
- Always break down the task into smaller subtasks and create intermediate columns to hold the data needed for generating the final result.
- For each subtask and final task, create a separate column with appropriate formulas.
- For each column, decide on the appropriate SheetCellType based on the expected data.
- Choose the most suitable formula type (Data Transformer or Processor Run) for each column that requires automatic data generation.
- When using Processor Run formulas:
  - Select the appropriate processor (GPT, Web search, or Document Reader) based on the column's purpose.
  - Construct the input and config dictionaries correctly, referencing other columns as needed.
  - Specify the correct jsonpath in the output_template to extract the desired data from the processor's output.
- For Data Transformer formulas, create an appropriate transformation_template using Shopify Liquid syntax.
- Use the `create_column` tool to add new columns to the sheet with the correct specifications.
- If updating existing columns, use the `update_cells` tool to modify cell values as needed.
- If the user's request is not clear, ask follow-up questions to gather all necessary information before proceeding with column creation or modification.
- Always create a step-by-step plan before implementing the columns, clearly outlining how each intermediate column contributes to the final result.
- Revisit your decisions and refine the column structure and formulas as needed before finalizing the sheet and responding to the user.

The current state of the sheet is as follows:

{<sheet_state>}


Let's think step by step to create the most effective column structure and formulas for the user's request. Always break down the task into smaller subtasks and create intermediate columns as needed.
"""

APP_DATA = {
    "name": "Super Agent",
    "config": {
        "seed": 32456,
        "model": "gpt-4o-mini",
        "stream": False,
        "max_steps": 20,
        "split_tasks": True,
        "temperature": 0.9,
        "user_message": "{{task}}",
        "chat_history_limit": 20,
    },
    "type_slug": "agent",
    "processors": [
        {
            "id": "send_suggested_messages",
            "name": "Send Suggested Messages",
            "input": {"stream": False, "input_str": "{{messages}}"},
            "config": {},
            "description": "Send suggested follow-up messages to the user",
            "input_fields": [
                {
                    "name": "messages",
                    "type": "array",
                    "title": "messages",
                    "description": "Suggested follow-up messages",
                    "items": {
                        "type": "string",
                    },
                },
            ],
            "provider_slug": "promptly",
            "processor_slug": "echo",
            "output_template": {"markdown": "Sent follow-up messages"},
        },
        {
            "id": "create_or_update_columns",
            "name": "Create or Update Columns using provided schema",
            "input": {"stream": False, "input_str": "{{json_schema}}"},
            "config": {},
            "description": "Create or update columns in the sheet using the provided schema",
            "input_fields": [
                {
                    "name": "columns",
                    "type": "array",
                    "title": "columns",
                    "description": "JSON schema for the columns",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "col_letter": {"type": "string"},
                            "cell_type": {"type": "integer"},
                            "width": {"type": "integer"},
                            "formula": {"type": "object"},
                        },
                    },
                },
            ],
            "provider_slug": "promptly",
            "processor_slug": "echo",
            "output_template": {"markdown": "Column created"},
        },
        {
            "id": "add_or_update_cells",
            "name": "Add or Update Cells",
            "input": {"stream": False, "input_str": "{{cells}}"},
            "config": {},
            "description": "Add or update the cells with the new values",
            "input_fields": [
                {
                    "name": "cells",
                    "type": "array",
                    "title": "cells",
                    "description": "Cells to add or update. Each cell is an object with the following properties: row, col_letter, value, spread_output",
                    "items": {
                        "type": "object",
                        "properties": {
                            "row": {"type": "integer"},
                            "col_letter": {"type": "string"},
                            "value": {"type": "string"},
                            "spread_output": {"type": "boolean"},
                        },
                    },
                },
            ],
            "provider_slug": "promptly",
            "processor_slug": "echo",
            "output_template": {"markdown": "Cells updated"},
        },
    ],
    "input_fields": [
        {
            "name": "task",
            "type": "multi",
            "title": "Task",
            "required": True,
            "allowFiles": True,
            "description": "What do you want the agent to perform?",
            "filesAccept": "image/*",
        }
    ],
    "output_template": {"markdown": "{{agent.content}}"},
}


class SheetBuilder:
    def __init__(self, sheet, user):
        self.sheet = sheet
        self.user = user
        self.model_provider_slug = MODEL_PROVIDER_SLUG
        self.model_slug = MODEL_SLUG
        self.session_id = str(uuid.uuid4())

        if not self.sheet:
            raise ValueError("Invalid sheet")

    async def _process_tool_call_chunks(self, response):
        chunks = response.get("chunks", [])
        tool_calls = []
        for chunk in chunks:
            if (
                "agent" in chunk
                and "content" in chunk.get("agent")
                and "arguments" in chunk.get("agent").get("content")
                and "name" in chunk.get("agent").get("content")
                and chunk["agent"]["content"]["name"]
                and chunk["agent"]["content"]["arguments"]
            ):
                tool_calls.append(chunk.get("agent").get("content"))

        return tool_calls

    async def run_agent(self, message):
        from llmstack.apps.apis import AppViewSet

        request = RequestFactory().post("/api/platform_apps/run", format="json")
        app_data = APP_DATA.copy()

        sheet_state = "Columns: \n" + ", ".join([column.model_dump_json() for column in self.sheet.columns])
        sheet_state += "\n\n"
        sheet_state += "Total rows: " + str(self.sheet.data.get("total_rows", 0))
        sheet_state += "\n\n"

        # Sample data from first 2 rows
        sheet_state += "Sample data from first 2 rows: \n"
        for i in range(1, 3):
            row_data = "Row " + str(i) + ": "
            for column in self.sheet.columns:
                cell = await sync_to_async(self.sheet.get_cell)(i, column.col_letter)
                row_data += str(cell) + " "
            sheet_state += row_data + "\n"

        app_data["config"]["system_message"] = MODEL_SYSTEM_MESSAGE.replace("{<sheet_state>}", sheet_state)
        request.data = {
            "stream": False,
            "app_data": app_data,
            "input": {"task": message},
            "detailed_response": True,
        }
        request.user = self.user

        # Run the agent
        response = await AppViewSet().run_platform_app_internal_async(
            session_id=self.session_id,
            request_uuid=str(uuid.uuid4()),
            request=request,
            preview=False,
        )
        return response

    async def process_event(self, event):
        event_type = event.get("type")
        if event_type == "connect":
            return event
        elif event_type == "message":
            try:
                response = await self.run_agent(event.get("message"))

                # Process tool call chunks
                tool_calls = await self._process_tool_call_chunks(response)

                return {"type": "message", "message": response.get("output", ""), "updates": tool_calls}
            except Exception as e:
                logger.error(f"Error running agent: {e}")
                return {"type": "message", "message": "Error running agent"}

        return event

    def close(self):
        pass
