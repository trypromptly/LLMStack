from typing import Annotated, Union

from pydantic import Field

from llmstack.data.transformations.splitters.csv import CSVTextSplitter
from llmstack.data.transformations.splitters.llamindex.splitters import (
    LlamIndexSentenceSplitter,
)

TransformationComponent = Annotated[
    Union[CSVTextSplitter, LlamIndexSentenceSplitter], Field(title="Transformation Component")
]
