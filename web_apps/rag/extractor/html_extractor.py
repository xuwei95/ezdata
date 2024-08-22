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
        file_path: str,
        ignore_links: bool = False,
        ignore_images: bool = False
    ):
        """Initialize with file path."""
        self._file_path = file_path
        self.ignore_links = ignore_links
        self.ignore_images = ignore_images

    def extract(self) -> list[Document]:
        return [Document(page_content=self._load_as_text())]

    def _load_as_text(self) -> str:
        with open(self._file_path, "rb") as fp:
            # 转为markdown格式
            html = fp.read().decode()
            text_maker = ht.HTML2Text()
            text_maker.bypass_tables = False
            text_maker.ignore_links = self.ignore_links
            text_maker.ignore_images = self.ignore_images
            text = text_maker.handle(html)
            return text
