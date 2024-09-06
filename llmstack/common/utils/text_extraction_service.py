import math
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

# from google.cloud import vision
from pydantic import BaseModel
from striprtf.striprtf import rtf_to_text
from unstructured.documents.elements import ElementMetadata, Text
from unstructured.partition.auto import partition_html
from unstructured.partition.doc import partition_doc
from unstructured.partition.docx import partition_docx
from unstructured.partition.epub import partition_epub
from unstructured.partition.image import partition_image
from unstructured.partition.md import partition_md
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.pptx import partition_pptx
from unstructured.partition.text import partition_text
from unstructured.partition.xlsx import partition_xlsx


class TextCanvas:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.canvas = [[" " for _ in range(width)] for _ in range(height)]

    def insert_text(self, text: str, x: int, y: int):
        if 0 <= y < self.height:
            for i, char in enumerate(text):
                pos = x + i
                if 0 <= pos < self.width:
                    if self.canvas[y][pos] != " ":
                        self.canvas[y][pos] = self._merge_characters(self.canvas[y][pos], char)
                    else:
                        self.canvas[y][pos] = char

    def _merge_characters(self, old_char, new_char):
        # In case of overlap, concatenate both characters
        return old_char + new_char

    def to_string(self) -> str:
        final_text = ""
        for row in self.canvas:
            row_text = "".join(row)
            if row_text.strip() == "":
                continue
            final_text += row_text + "\n"
        return final_text


class BoundingBox(BaseModel):
    top_left: Tuple[float, float]
    top_right: Tuple[float, float]
    bottom_left: Tuple[float, float]
    bottom_right: Tuple[float, float]


class PageElement(BaseModel):
    text: str = ""
    coordinates: Optional[BoundingBox] = None
    normalized_midpoint: Optional[Tuple[float, float]] = (None, None)
    provider_data: Optional[Dict[str, Any]] = None

    @property
    def midpoint(self):
        if self.coordinates and self.coordinates.bottom_left:
            return (self.coordinates.bottom_left[0], self.coordinates.bottom_left[1])
        return None

    @property
    def width(self):
        if self.coordinates and self.coordinates.top_right and self.coordinates.top_left:
            return self.coordinates.top_right[0] - self.coordinates.top_left[0]
        return None

    @property
    def height(self):
        if self.coordinates and self.coordinates.bottom_left and self.coordinates.top_left:
            return self.coordinates.bottom_left[1] - self.coordinates.top_left[1]

    def set_midpoint_normalized(self, page_width: float, page_height: float):
        self.normalized_midpoint = (
            (self.midpoint[0] / page_width, self.midpoint[1] / page_height) if self.midpoint else None
        )


class Page(BaseModel):
    elements: List[PageElement] = []
    page_no: int = 1
    width: Optional[int] = None
    height: Optional[int] = None
    page_metadata: Optional[Dict[str, Any]] = None
    font_height: Optional[int] = None
    font_width: Optional[int] = None

    @property
    def text(self):
        return "\n".join([element.text for element in self.elements])

    @property
    def formatted_text(self):
        if self.width and self.height and self.font_height and self.font_width:
            text_canvas_width = int(self.width / self.font_width)
            text_canvas_height = int(self.height / self.font_height)
            text_canvas = TextCanvas(width=text_canvas_width, height=text_canvas_height)
            for element in self.elements:
                x = int(element.normalized_midpoint[0] * text_canvas_width)
                y = int(element.normalized_midpoint[1] * text_canvas_height)
                text_canvas.insert_text(element.text, x, y)
            return text_canvas.to_string()
        return self.text


class TextractResponse(BaseModel):
    pages: List[Page] = []

    @property
    def text(self):
        return "\n".join([page.text for page in self.pages])

    @property
    def formatted_text(self):
        text = ""
        for page in self.pages:
            text += page.formatted_text
            text += f"\n--- Page Break (Pg {page.page_no})---\n"
        return text


class TextExtractionService(ABC):
    def __init__(self, provider) -> None:
        self._provider = provider

    @abstractmethod
    def extract_from_bytes(self, file: bytes, **kwargs) -> TextractResponse:
        pass

    @abstractmethod
    def extract_from_uri(self, file_uri: bytes) -> TextractResponse:
        pass


# class GoogleVisionTextExtractionService(TextExtractionService):
#     def __init__(self, credentials: Dict[str, Any], provider: str = "google") -> None:
#         super().__init__(provider)

#         try:
#             self.client = vision.ImageAnnotatorClient.from_service_account_info(credentials)
#         except Exception:
#             raise ValueError("Invalid credentials")

#         text_detection = vision.Feature()
#         text_detection.type_ = vision.Feature.Type.TEXT_DETECTION
#         self._features = [text_detection]

#     def extract_from_bytes(self, file: bytes, **kwargs) -> TextractResponse:
#         request = vision.AnnotateImageRequest()
#         image = vision.Image()
#         image.content = file
#         request.image = image
#         request.features = self._features

#         res = self.client.annotate_image(request)

#         annotations = res.text_annotations
#         if len(annotations) == 0:
#             return TextractResponse(annotations=[], pages=[], formatted_pages=[])

#         whole_text_box_max = annotations[0].bounding_poly.vertices[2]
#         max_width = whole_text_box_max.x
#         max_height = whole_text_box_max.y

#         result = TextractResponse()
#         annotations = []
#         for text in annotations[1:]:
#             box = text.bounding_poly.vertices

#             # use the bottom left coordinate as the "midpoint"
#             midpoint = (box[3].x, box[3].y)

#             annotations.append(
#                 ImageAnnotation(
#                     text=text.description,
#                     midpoint=midpoint,
#                     midpoint_normalized=(midpoint[0] / max_width, midpoint[1] / max_height),
#                     width=box[1].x - box[0].x,
#                     height=box[2].y - box[0].y,
#                 )
#             )

#         annotations = list(
#             sorted(
#                 annotations,
#                 key=lambda x: (
#                     x.midpoint_normalized[1],
#                     x.midpoint_normalized[0],
#                 ),
#             )
#         )
#         result.annotations = annotations

#         return result

#     def extract_from_uri(self, file_uri: bytes) -> TextractResponse:
#         from llmstack.common.utils.utils import validate_parse_data_uri

#         mime_type, filename, data = validate_parse_data_uri(file_uri)
#         return super().extract_from_uri(data)


class PromptlyTextExtractionService(TextExtractionService):
    def __init__(self, provider: str = "promptly") -> None:
        super().__init__(provider)

    def extract_from_bytes(self, file: bytes, **kwargs) -> TextractResponse:
        mime_type = kwargs["mime_type"]
        file_name = kwargs["filename"]
        data_fp = BytesIO(file)
        elements = []
        pages = {}
        if mime_type == "application/pdf":
            elements = partition_pdf(file=data_fp)
        elif mime_type == "application/rtf" or mime_type == "text/rtf":
            elements = partition_text(text=rtf_to_text(file.decode("utf-8")))
        elif mime_type == "text/plain":
            elements = partition_text(text=file.decode("utf-8"))
        elif mime_type == "application/json":
            elements = [
                Text(
                    text=file.decode("utf-8"),
                    metadata=ElementMetadata(filename=file_name),
                ),
            ]
        elif mime_type == "text/csv" or mime_type == "application/csv":
            elements = [
                Text(
                    text=file.decode("utf-8"),
                    metadata=ElementMetadata(filename=file_name),
                ),
            ]
        elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            elements = partition_xlsx(file=data_fp)
        elif mime_type == "application/msword":
            elements = partition_doc(file=data_fp)
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            elements = partition_docx(file=data_fp)
        elif mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            elements = partition_pptx(file=data_fp)
        elif mime_type == "application/vnd.ms-powerpoint":
            raise Exception(
                "Unsupported file type .ppt please convert it to .pptx",
            )
        elif mime_type == "image/jpeg" or mime_type == "image/png":
            elements = partition_image(file=data_fp)
        elif mime_type == "text/html":
            elements = partition_html(file=data_fp)
        elif mime_type == "application/epub+zip":
            elements = partition_epub(file=data_fp)
        elif mime_type == "text/markdown":
            elements = partition_md(text=file.decode("utf-8"))
        else:
            raise Exception("Unsupported file type")

        if not elements:
            return TextractResponse(pages=[])

        font_height = None
        font_width = None
        for element in elements:
            page_number = element.metadata.page_number or 1
            if page_number not in pages:
                pages[page_number] = Page(
                    page_no=page_number,
                    page_metadata={"mime_type": mime_type, "filename": file_name},
                    width=None,
                    height=None,
                )
            page = pages[page_number]
            if not (page.width or page.height):
                if element.metadata.coordinates and element.metadata.coordinates.system:
                    if element.metadata.coordinates.system.width:
                        page.width = element.metadata.coordinates.system.width

                    if element.metadata.coordinates.system.height:
                        page.height = element.metadata.coordinates.system.height
            page_element = PageElement(text=element.text, provider_data=element.to_dict())
            print(element.to_dict())
            if element.metadata.coordinates and element.metadata.coordinates.points:
                page_element.coordinates = BoundingBox(
                    top_left=(element.metadata.coordinates.points[0][0], element.metadata.coordinates.points[0][1]),
                    bottom_left=(element.metadata.coordinates.points[1][0], element.metadata.coordinates.points[1][1]),
                    bottom_right=(element.metadata.coordinates.points[2][0], element.metadata.coordinates.points[2][1]),
                    top_right=(element.metadata.coordinates.points[3][0], element.metadata.coordinates.points[3][1]),
                )
            if page_element.text:
                font_height = (
                    min(page_element.height, font_height)
                    if font_height
                    else page_element.height
                    if page_element.height
                    else None
                )
                font_width = (
                    min(page_element.width / len(page_element.text), font_width)
                    if font_width
                    else (page_element.width / len(page_element.text))
                    if page_element.width
                    else None
                )
            if page.width and page.height:
                page_element.set_midpoint_normalized(page.width, page.height)
            page.elements.append(page_element)

        for page_number, page in pages.items():
            page.elements = sorted(page.elements, key=lambda x: (x.normalized_midpoint[1], x.normalized_midpoint[0]))
            page.font_height = math.ceil(font_height) if font_height else None
            page.font_width = math.ceil(font_width) if font_width else None

        return TextractResponse(pages=list(pages.values()))

    def extract_from_uri(self, file_uri: bytes) -> TextractResponse:
        from llmstack.common.utils.utils import validate_parse_data_uri

        # Extract text from URI
        mime_type, filename, data = validate_parse_data_uri(file_uri)
        return super().extract_from_uri(data, mime_type=mime_type, filename=filename)


if __name__ == "__main__":
    service = PromptlyTextExtractionService()
    with open(
        "/Users/vigneshaigal/Projects/makerdojo/promptmanager/llmstack/llmstack/common/tests/fixtures/sample.docx",
        "rb",
    ) as f:
        response = service.extract_from_bytes(
            f.read(),
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="sample.docx",
        )
        for page in response.pages:
            print(page.formatted_text)
