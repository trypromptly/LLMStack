import logging
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Union

from jsonpath_ng import parse
from promptly.core.base import BaseConfiguration
from promptly.core.base import BaseConfigurationType
from promptly.core.base import BaseInput
from promptly.core.base import BaseInputType
from promptly.core.base import BaseOutput
from promptly.core.base import BaseOutputType
from promptly.core.base import BaseProcessor
from pydantic import Field
from pydantic import validator


logger = logging.getLogger(__name__)


class DataTransformerProcessorInput(BaseInput):
    input: Dict[
        str, Union[
            str, int, float, bool, List[str],
            List[int], List[float], List[bool],
        ],
    ]


class DataTransformerProcessorOutput(BaseOutput):
    output: Dict[
        str, Optional[
            Union[
                str, int, float, bool, List[str],
                List[int], List[float], List[bool],
            ]
        ],
    ]


class DataTransformerProcessorConfiguration(BaseConfiguration):
    mapper: Dict[str, str] = Field(
        ...,
        description='Mapper to transform the input data', example={'username': '$.name'},
    )

    @validator('mapper')
    def validate_mapper(cls, v):
        for key, value in v.items():
            try:
                parse(value)
            except Exception as e:
                raise ValueError(f'Invalid jsonpath expression: {value}')
        return v


class DataTransformerProcessor(BaseProcessor[DataTransformerProcessorInput, DataTransformerProcessorOutput, DataTransformerProcessorConfiguration], Generic[BaseInputType, BaseOutputType, BaseConfigurationType]):
    """
    # DataTransformerProcessor

    The `DataTransformerProcessor` is a processor that helps to transform input JSON data to a new JSON dictionary using JSONPath expressions. The JSONPath expressions are defined in the configuration.

    ## Classes

    ### DataTransformerProcessorInput

    This class inherits from `BaseInput` and represents the input for the DataTransformerProcessor.

    Attributes:

    - `input`: A dictionary with values of different types (str, int, float, bool, List[str], List[int], List[float], List[bool]).

    ### DataTransformerProcessorOutput

    This class inherits from `BaseOutput` and represents the output of the DataTransformerProcessor.

    Attributes:

    - `output`: A dictionary with Optional values of different types (str, int, float, bool, List[str], List[int], List[float], List[bool]).

    ### DataTransformerProcessorConfiguration

    This class inherits from `BaseConfiguration` and represents the configuration for the DataTransformerProcessor.

    Attributes:

    - `mapper`: A dictionary with JSONPath expressions to transform the input data (default: ...). Example: `{"username": "$.name"}`.

    Methods:

    - `validate_mapper(cls, v)`: Validates the mapper attribute.

    ### DataTransformerProcessor

    This class inherits from `BaseProcessor` and represents the main
    """

    def _process(self,  input: DataTransformerProcessorInput, configuration: DataTransformerProcessorConfiguration) -> DataTransformerProcessorOutput:
        """
            Invokes the processor on the input and returns the output
        """
        output = {}
        for key, value in configuration.mapper.items():
            jsonpath_expr = parse(value)
            matches = jsonpath_expr.find(input.input)
            if len(matches) > 0:
                output[key] = matches[0].value
            else:
                output[key] = None
        return DataTransformerProcessorOutput(output=output)
