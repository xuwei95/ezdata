import os
import requests
from tempfile import NamedTemporaryFile
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse
from web_apps.rag.extractor.extractor_base import BaseExtractor
from langchain_core.documents import Document
from web_apps.rag.extractor.csv_extractor import CSVExtractor
from web_apps.rag.extractor.excel_extractor import ExcelExtractor
from web_apps.rag.extractor.html_extractor import HtmlExtractor
from web_apps.rag.extractor.markdown_extractor import MarkdownExtractor
from web_apps.rag.extractor.pdf_extractor import PdfExtractor
from web_apps.rag.extractor.word_extractor import WordExtractor


def extract_links_from_markdown(markdown_content):
    # 使用正则表达式匹配Markdown格式的链接
    link_pattern = re.compile(r'\[.*?\]\((.*?)\)')
    links = link_pattern.findall(markdown_content)
    return links


class HttpUrlExtractor(BaseExtractor):

    """
    Load url content.
    """

    def __init__(
            self,
            url,
            headers=None,
            ignore_links: bool = False,
            ignore_images: bool = False,
            mode: str = 'scrape',
            max_depth: int = 3
    ):
        """Initialize with url."""
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
            }
        self._url = url
        self._headers = headers
        self.ignore_links = ignore_links
        self.ignore_images = ignore_images
        self.mode = mode
        self.max_depth = max_depth
        self.visited_urls = set()  # 用于存储已经访问过的URL

    def extract(self) -> list[Document]:
        if self.mode == 'crawl':
            return self._crawl(self._url, depth=0)
        else:
            return self._scrape(self._url)

    def _scrape(self, url) -> list[Document]:
        url_suffix = Path(url).suffix

        # Use requests to get the content and a NamedTemporaryFile to store it
        with requests.get(url, headers=self._headers, stream=True) as response, \
                NamedTemporaryFile(delete=False, suffix=url_suffix) as temp_file:
            try:
                # Check if the request was successful
                response.raise_for_status()

                # Write the content to the temporary file
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)

                file_path = str(Path(temp_file.name))
                # Now, 'temp_file.name' contains the path to the temporary file with the content downloaded
                input_file = Path(file_path)
                file_extension = input_file.suffix.lower()
                if file_extension == '.xlsx' or file_extension == '.xls':
                    extractor = ExcelExtractor(file_path)
                elif file_extension == '.pdf':
                    extractor = PdfExtractor(file_path)
                elif file_extension in ['.md', '.markdown']:
                    extractor = MarkdownExtractor(file_path, autodetect_encoding=True)
                elif file_extension in ['.docx']:
                    extractor = WordExtractor(file_path)
                elif file_extension == '.csv':
                    extractor = CSVExtractor(file_path, autodetect_encoding=True)
                else:
                    extractor = HtmlExtractor(file_path, ignore_links=self.ignore_links,
                                              ignore_images=self.ignore_images)
                documents = extractor.extract()
                # Close the file after writing to ensure all data is written
                temp_file.close()
            finally:
                os.unlink(file_path)
            return documents

    def _crawl(self, url, depth) -> list[Document]:
        if depth > self.max_depth:
            return []

        if url in self.visited_urls:
            return []
        self.visited_urls.add(url)

        documents = self._scrape(url)

        if isinstance(documents, list) and len(documents) > 0:
            for doc in documents:
                links = extract_links_from_markdown(doc.page_content)
                links = [i for i in links if i != '' and i[0] == '/']
                for link in links:
                    absolute_url = urljoin(url, link)
                    if urlparse(absolute_url).netloc == urlparse(url).netloc:
                        documents.extend(self._crawl(absolute_url, depth + 1))

        return documents


if __name__ == '__main__':
    url = 'http://ezdata.cloud'
    extractor = HttpUrlExtractor(url, mode='crawl', max_depth=3)
    documents = extractor.extract()
    print(documents)