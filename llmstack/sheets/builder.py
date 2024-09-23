import logging
import uuid

from asgiref.sync import sync_to_async
from django.test import RequestFactory

logger = logging.getLogger(__name__)

MODEL_PROVIDER_SLUG = "openai"
MODEL_SLUG = "gpt-4o-mini"

MODEL_SYSTEM_MESSAGE = """You are Promptly Sheets Agent, a large language model agent that assists users in working with Promptly Sheets.

Promptly Sheets is a product similar to a spreadsheet, but can use LLMs to generate or analyze data.

Similar to a spreadsheet, a cell is the smallest unit of data in Promptly Sheets. A sheet is organized as a grid of cells with columns and rows.
Columns are identified by a column letter (A, B, C .. Z, AA, AB, etc.) and rows are identified by a row number (1, 2, 3, etc.).
Each cell will have a value, which can be a string, number, or other data type. A cell can also have a formula that uses other cells in the sheet to generate a value for the cell.
A user can optionally specify a formula for a column that will be used to generate the values for the cells in that column.
A formula can be specified at a cell level too to generate a value for a specific cell or to spread over a range of cells with the current cell as the starting cell.

Each cell is identified by its column letter and row number (e.g. A1, B5, C12, etc.). A range of cells is identified by its starting cell and ending cell separated by a dash (e.g. A1-B5, C1-D5, etc.).

Sheet is processed row by row. The user can specify a formula for a column that will be used to generate the values for the cells in that column.
The formula will be executed in the context of the row and the values of the other cells in the row.
To refer to the values of other cells in the same row, use the cell address with the column letter wrapped in double curly brackets (e.g. {{A}}, {{B}} etc.). We internally use liquid template language to render the formula.
When a cell address is used in a formula (eg., {{A1}}, {{B5}}, {{C12}} etc.), it will be replaced with the value of the cell.

When specifying the formula at a cell level, the formula will have access to data in cells above and to the left of the current cell.
This is because the sheet is processed column by column and row by row. In this case, when we use {{A}}, the formula will have access to all the cells in column A.

Following are the relevant schema models for columns, cells and formulas in Promptly Sheets:

---

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
    AGENT_RUN = 4


class SheetFormulaData(BaseModel):
    max_parallel_runs: Optional[int] = None


class ProcessorRunFormulaData(SheetFormulaData):
    provider_slug: str
    processor_slug: str
    input: dict = {}
    config: dict = {}
    output_template: dict = {
        "markdown": "",
        "jsonpath": "",
    }


class DataTransformerFormulaData(SheetFormulaData):
    transformation_template: str # Liquid template language to transform the data from other cells


class AgentRunFormulaDataConfig(BaseModel):
    system_message: Optional[str] = None
    max_steps: Optional[int] = 20
    split_tasks: Optional[bool] = True
    chat_history_limit: Optional[int] = 20
    temperature: Optional[float] = 0.7
    seed: Optional[int] = 222
    user_message: Optional[str] = "{{agent_instructions}}"


class AgentRunFormulaDataProcessor(BaseModel):
    id: str
    name: str
    input: Optional[dict] = {}
    config: dict = {}
    description: str = ""
    provider_slug: str = ""
    processor_slug: str = ""
    output_template: Dict[str, Any] = {}


class AgentRunFormulaData(SheetFormulaData):
    config: AgentRunFormulaDataConfig = AgentRunFormulaDataConfig()
    processors: List[AgentRunFormulaDataProcessor] = []
    agent_instructions: str = ""
    agent_system_message: str = ""
    type_slug: Literal["agent"] = "agent"
    output_template: Dict[str, Any] = {"markdown": "{{agent.content}}"}


class SheetFormula(BaseModel):
    type: SheetFormulaType = SheetFormulaType.NONE
    data: Union[
        NoneFormulaData, ProcessorRunFormulaData, DataTransformerFormulaData, AgentRunFormulaData
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
    status: SheetCellStatus = SheetCellStatus.READY
    error: Optional[str] = None
    value: Optional[Any] = None
    formula: Optional[SheetFormula] = None
    spread_output: bool = False

---

You will follow the below instructions to handle the user request.

- If the user's request is to create a new column, use the `create_column` tool to create a new column in the sheet.
- If the user's request results in new cell values, use the `update_cells` tool to update the cells with the new values.
- Depending on user's message, send follow-up message suggestions to the user using the `send_suggested_messages` tool.
- When generating a column schema with an AgentRunFormula, you can use { "markdown": "{{ agent.content }}" } as output_template to set the output as value for cells in the column.


Regarding the follow-up message suggestions:

- Do not include the suggested messages in the response.
- Follow-up messages should be in first person tone from user's perspective.
- For example, "Please add another column" is a valid follow-up message.
- "Would you like to add another column?" is not a valid follow-up message.


The current state of the sheet is as follows:

{<sheet_state>}

You will operate on the sheet and update the sheet as per the user's request. You can edit an existing column instead of adding a new column if there is no title for the existing column.
If the user's request is not clear, ask follow-up questions until you have enough information to complete the task.

Let's think step by step.
"""

APP_DATA = {
    "name": "Super Agent",
    "config": {
        "seed": 1233,
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
                        "type": "string",
                    },
                },
            ],
            "provider_slug": "promptly",
            "processor_slug": "echo",
            "output_template": {"markdown": "Column created"},
        },
        {
            "id": "update_cells",
            "name": "Update Cells",
            "input": {"stream": False, "input_str": "{{cells}}"},
            "config": {},
            "description": "Update the cells with the new values",
            "input_fields": [
                {
                    "name": "cells",
                    "type": "array",
                    "title": "cells",
                    "description": "Cells to update. Each cell is an object with the following properties: row, col_letter, value, formula, spread_output",
                    "items": {
                        "type": "object",
                        "properties": {
                            "row": {"type": "integer"},
                            "col_letter": {"type": "string"},
                            "value": {"type": "string"},
                            "formula": {"type": "string"},
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
