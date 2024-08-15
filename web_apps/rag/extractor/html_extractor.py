"""Abstract interface for document loader implementations."""
from web_apps.rag.extractor.extractor_base import BaseExtractor
from langchain_core.documents import Document
import html2text as ht


class HtmlExtractor(BaseExtractor):

    """
    Load html files.


    Args:
        file_path: Path to the file to load.
    """

    def __init__(
        self,
        file_path: str
    ):
        """Initialize with file path."""
        self._file_path = file_path

    def extract(self) -> list[Document]:
        return [Document(page_content=self._load_as_text())]

    def _load_as_text(self) -> str:
        with open(self._file_path, "rb") as fp:
            # 转为markdown格式
            html = fp.read().decode()
            text_maker = ht.HTML2Text()
            text_maker.bypass_tables = False
            text_maker.ignore_links = False
            text_maker.ignore_images = False
            text = text_maker.handle(html)
            return text
