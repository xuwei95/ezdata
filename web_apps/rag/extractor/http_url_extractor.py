import os
import requests
from tempfile import NamedTemporaryFile
from pathlib import Path
from web_apps.rag.extractor.extractor_base import BaseExtractor
from langchain_core.documents import Document
from web_apps.rag.extractor.csv_extractor import CSVExtractor
from web_apps.rag.extractor.excel_extractor import ExcelExtractor
from web_apps.rag.extractor.html_extractor import HtmlExtractor
from web_apps.rag.extractor.markdown_extractor import MarkdownExtractor
from web_apps.rag.extractor.pdf_extractor import PdfExtractor
from web_apps.rag.extractor.word_extractor import WordExtractor


class HttpUrlExtractor(BaseExtractor):

    """
    Load url content.
    """

    def __init__(
            self,
            url,
            headers=None
    ):
        """Initialize with url."""
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
            }
        self._url = url
        self._headers = headers

    def extract(self) -> list[Document]:
        url_suffix = Path(self._url).suffix

        # Use requests to get the content and a NamedTemporaryFile to store it
        with requests.get(self._url, headers=self._headers, stream=True) as response, \
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
                    extractor = HtmlExtractor(file_path)
                documents = extractor.extract()
                # Close the file after writing to ensure all data is written
                temp_file.close()
            finally:
                os.unlink(file_path)
            return documents


if __name__ == '__main__':
    url = 'https://akshare.akfamily.xyz/data/stock/stock.html'
    extractor = HttpUrlExtractor(url)
    documents = extractor.extract()
    print(documents)