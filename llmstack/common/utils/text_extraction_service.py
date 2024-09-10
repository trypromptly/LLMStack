import base64
import math
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel
from striprtf.striprtf import rtf_to_text
from unstructured.documents.elements import ElementMetadata, PageBreak, Text
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


def table_html_to_text(table_html: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(table_html, "html.parser")
    text = ""
    for row in soup.find_all("tr"):
        for cell in row.find_all(["td", "th"]):
            text += cell.get_text() + " "
        text += "\n"
    return text


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

    def _remove_empty_rows(self):
        row_str = ""
        for row in self.canvas:
            for col in row:
                row_str += col
            if row_str.strip() == "":
                self.canvas.remove(row)

    def _remove_empty_columns(self):
        for i in range(self.width):
            col_str = ""
            for row in self.canvas:
                col_str += row[i]
            if col_str.strip() == "":
                for row in self.canvas:
                    row[i] = ""

    def _merge_characters(self, old_char, new_char):
        # In case of overlap, concatenate both characters
        return old_char + new_char

    def to_string(self) -> str:
        final_text = ""
        self._remove_empty_columns()
        self._remove_empty_rows()
        for row in self.canvas:
            row_text = "".join(row)
            if row_text.strip() != "":
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
    element_type: Optional[str] = None

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

    @property
    def formatted_text(self):
        if self.provider_data and self.provider_data.get("type") == "Table":
            if self.provider_data.get("metadata", {}).get("text_as_html"):
                return table_html_to_text(self.provider_data.get("metadata", {}).get("text_as_html"))
        return self.text


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
        else:
            return "\n".join([element.formatted_text for element in self.elements])


class TextractResponse(BaseModel):
    pages: List[Page] = []
    file_name: Optional[str] = None
    _full_text: Optional[str] = None

    @property
    def text(self):
        if self._full_text:
            return self._full_text
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


class GoogleVisionTextExtractionService(TextExtractionService):
    def __init__(self, service_account_json, provider: str = "google") -> None:
        from google.cloud import vision

        super().__init__(provider)

        try:
            self.client = vision.ImageAnnotatorClient.from_service_account_info(service_account_json)
        except Exception:
            raise ValueError("Invalid credentials")

        text_deteection_feature = vision.Feature()
        text_deteection_feature.type_ = vision.Feature.Type.TEXT_DETECTION
        self._features = [text_deteection_feature]

    def extract_from_bytes(self, file: bytes, **kwargs) -> TextractResponse:
        from google.cloud import vision

        request = vision.AnnotateImageRequest(image=vision.Image(content=file), features=self._features)
        res = self.client.annotate_image(request)

        response = TextractResponse(pages=[], file_name=kwargs.get("filename"))
        if res.text_annotations:
            page_width = res.text_annotations[0].bounding_poly.vertices[2].x
            page_height = res.text_annotations[0].bounding_poly.vertices[2].y
            page = Page(page_no=1, width=page_width, height=page_height)
            font_height = None
            font_width = None

            for text_annotation in res.text_annotations[1:]:
                if text_annotation.description:
                    text_annotation_text = text_annotation.description
                    box = text_annotation.bounding_poly.vertices
                    font_height = (
                        min(box[2].y - box[0].y, font_height)
                        if font_height
                        else box[2].y - box[0].y
                        if box[2].y - box[0].y
                        else None
                    )
                    font_width = (
                        min((box[1].x - box[0].x) / len(text_annotation_text), font_width)
                        if font_width
                        else (
                            (box[1].x - box[0].x) / len(text_annotation_text)
                            if (box[1].x - box[0].x) / len(text_annotation_text)
                            else None
                        )
                    )
                    page_element = PageElement(
                        text=text_annotation.description,
                        coordinates=BoundingBox(
                            top_left=(box[0].x, box[0].y),
                            top_right=(box[1].x, box[1].y),
                            bottom_right=(box[2].x, box[2].y),
                            bottom_left=(box[3].x, box[3].y),
                        ),
                    )
                    page_element.set_midpoint_normalized(page_width, page_height)
                    page.elements.append(page_element)
            page.elements = sorted(page.elements, key=lambda x: (x.normalized_midpoint[1], x.normalized_midpoint[0]))
            page.font_height = math.ceil(font_height) if font_height else None
            page.font_width = math.ceil(font_width) if font_width else None
            response.pages.append(page)
        elif res.full_text_annotation:
            response._full_text = res.full_text_annotation.text
            for page_number, annotated_page in enumerate(res.full_text_annotation.pages, start=1):
                font_height = None
                font_width = None
                page = Page(page_no=page_number, width=annotated_page.width, height=annotated_page.height)
                for annotated_page_block in annotated_page.blocks:
                    if annotated_page_block.block_type == vision.Block.BlockType.TEXT:
                        for annotated_page_block_paragraph in annotated_page_block.paragraphs:
                            for annotated_page_block_paragraph_word in annotated_page_block_paragraph.words:
                                word_text = ""
                                word_height = abs(
                                    annotated_page_block_paragraph_word.bounding_box.vertices[2].y
                                    - annotated_page_block_paragraph_word.bounding_box.vertices[0].y
                                )
                                word_width = abs(
                                    annotated_page_block_paragraph_word.bounding_box.vertices[1].x
                                    - annotated_page_block_paragraph_word.bounding_box.vertices[0].x
                                )
                                for (
                                    annotated_page_block_paragraph_word_symbol
                                ) in annotated_page_block_paragraph_word.symbols:
                                    if annotated_page_block_paragraph_word_symbol.text:
                                        word_text += annotated_page_block_paragraph_word_symbol.text
                                if word_text:
                                    font_height = (
                                        min(word_height, font_height)
                                        if font_height
                                        else word_height
                                        if word_height
                                        else None
                                    )
                                    font_width = (
                                        min(int(word_width / len(word_text)), font_width)
                                        if font_width
                                        else (
                                            int(word_width / len(word_text))
                                            if int(word_width / len(word_text))
                                            else None
                                        )
                                    )
                                page_element = PageElement(
                                    text=word_text,
                                    coordinates=BoundingBox(
                                        top_left=(
                                            annotated_page_block_paragraph_word.bounding_box.vertices[0].x,
                                            annotated_page_block_paragraph_word.bounding_box.vertices[0].y,
                                        ),
                                        top_right=(
                                            annotated_page_block_paragraph_word.bounding_box.vertices[1].x,
                                            annotated_page_block_paragraph_word.bounding_box.vertices[1].y,
                                        ),
                                        bottom_right=(
                                            annotated_page_block_paragraph_word.bounding_box.vertices[2].x,
                                            annotated_page_block_paragraph_word.bounding_box.vertices[2].y,
                                        ),
                                        bottom_left=(
                                            annotated_page_block_paragraph_word.bounding_box.vertices[3].x,
                                            annotated_page_block_paragraph_word.bounding_box.vertices[3].y,
                                        ),
                                    ),
                                )
                                page_element.set_midpoint_normalized(page.width, page.height)
                                page.elements.append(page_element)
                    elif annotated_page_block.block_type == vision.Block.BlockType.TABLE:
                        pass

                page.elements = sorted(
                    page.elements, key=lambda x: (x.normalized_midpoint[1], x.normalized_midpoint[0])
                )
                page.font_height = math.ceil(font_height) if font_height else None
                page.font_width = math.ceil(font_width) if font_width else None
                response.pages.append(page)

        return response

    def extract_from_uri(self, file_uri: bytes) -> TextractResponse:
        from llmstack.common.utils.utils import validate_parse_data_uri

        mime_type, filename, data = validate_parse_data_uri(file_uri)
        return self.extract_from_bytes(base64.b64decode(data), mime_type=mime_type, filename=filename)


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
            elements = partition_pdf(file=data_fp, include_page_breaks=True, infer_table_structure=False)
        elif mime_type == "application/rtf" or mime_type == "text/rtf":
            elements = partition_text(text=rtf_to_text(file.decode("utf-8")))
        elif mime_type == "text/plain":
            elements = partition_text(text=file.decode("utf-8"))
        elif mime_type == "application/json":
            elements = [Text(text=file.decode("utf-8"), metadata=ElementMetadata(filename=file_name))]
        elif mime_type == "text/csv" or mime_type == "application/csv":
            elements = [Text(text=file.decode("utf-8"), metadata=ElementMetadata(filename=file_name))]
        elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            elements = partition_xlsx(file=data_fp)
        elif mime_type == "application/msword":
            elements = partition_doc(file=data_fp)
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            elements = partition_docx(file=data_fp)
        elif mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            elements = partition_pptx(file=data_fp)
        elif mime_type == "image/jpeg" or mime_type == "image/png":
            elements = partition_image(file=data_fp)
        elif mime_type == "text/html":
            elements = partition_html(file=data_fp)
        elif mime_type == "application/epub+zip":
            elements = partition_epub(file=data_fp)
        elif mime_type == "text/markdown":
            elements = partition_md(text=file.decode("utf-8"), include_page_breaks=True)
        else:
            raise Exception("Unsupported file type")

        if not elements:
            return TextractResponse(pages=[], file_name=file_name)

        font_height = None
        font_width = None
        page_number = 1
        for element in elements:
            if isinstance(element, PageBreak):
                page_number += 1
                continue
            page_number = element.metadata.page_number or page_number
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
            page_element = PageElement(
                text=element.text, provider_data=element.to_dict(), element_type=element.category
            )
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

        return TextractResponse(pages=list(pages.values()), file_name=file_name)

    def extract_from_uri(self, file_uri: str) -> TextractResponse:
        from llmstack.common.utils.utils import validate_parse_data_uri

        # Extract text from URI
        mime_type, filename, data = validate_parse_data_uri(file_uri)

        return self.extract_from_bytes(base64.b64decode(data), mime_type=mime_type, filename=filename)
