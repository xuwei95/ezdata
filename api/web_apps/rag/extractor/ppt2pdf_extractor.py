import logging
from typing import Optional
from web_apps.rag.extractor.extractor_base import BaseExtractor
from langchain_core.documents import Document
from utils.storage_utils import storage
import subprocess
import tempfile
from pptx import Presentation
import fitz
from unstructured.partition.pptx import partition_pptx
from unstructured.documents.elements import ElementType
from utils.common_utils import gen_uuid
logger = logging.getLogger(__name__)


def convert_file(input_path, output_format: str):
    process = None
    try:
        process = subprocess.Popen(['/usr/bin/unoconv', '-f', output_format, '--stdout', bytes(), input_path],
                                   stdout=subprocess.PIPE)
        output, _ = process.communicate(timeout=90)
        logging.info(f"covert pptx to pdf success, path = {input_path}")
        return output
    except Exception as e:
        if process is not None:
            process.kill()
        return None


def parse_pptx_to_pdf(file, parse_hidden_pages: bool):
    has_hidden_pages = False
    if parse_hidden_pages:
        prs = Presentation(file)
        for slide in prs.slides:
            show = slide._element.get("show")
            if show == '0':
                has_hidden_pages = True
                slide._element.set("show", '1')
        if has_hidden_pages:
            with tempfile.NamedTemporaryFile(suffix='.pptx') as tmp_file:
                prs.save(tmp_file.name)
                converted_output = convert_file(tmp_file.name, 'pdf')
                return converted_output
    converted_output = convert_file(file, 'pdf')
    return converted_output


def parse_pdf_to_images(file, parse_hidden_pages: bool):
    converted_output = parse_pptx_to_pdf(file, parse_hidden_pages)
    stream_list = []
    pdf_doc = fitz.open(stream=converted_output, filetype="pdf")
    for page_number in range(pdf_doc.page_count):
        page = pdf_doc.load_page(page_number)
        image = page.get_pixmap(dpi=300)
        tmp_bytes = image.pil_tobytes(format="png", optimize=True)
        save_file_key = f"{gen_uuid()}.png"
        storage.save(save_file_key, tmp_bytes)
        url = storage.get_download_url(save_file_key)
        stream_list.append(url)
    pdf_doc.close()
    html_tag_dict = {}
    for i in range(len(stream_list)):
        url = stream_list[i]
        html_tag = f'< img src="{url}">'
        html_tag_dict[i + 1] = html_tag
    logging.info(f"convert pdf to images success, path = {file}")
    return html_tag_dict


class PptExtractor(BaseExtractor):
    """Load ppt files.


    Args:
        file_path: Path to the file to load.
    """

    def __init__(
            self,
            file_path: str,
            file_cache_key: Optional[str] = None,
            parser_image: Optional[bool] = True
    ):
        """Initialize with file path."""
        self._file_path = file_path
        self._file_cache_key = file_cache_key
        self.parser_hidden_pages = True
        self.parser_image = parser_image
        self.html_tag_dict = {}


    def extract(self) -> list[Document]:
        documents = []
        # 按页生成图片
        elements = partition_pptx(self._file_path, include_page_breaks=True)
        # 解析图片
        if self.parser_image:
            self.html_tag_dict = parse_pdf_to_images(self._file_path, self.parser_hidden_pages)
        for e in elements:
            if e.category == "PageBreak":
                continue
            if e.category == ElementType.TABLE:
                e.text = e.metadata.text_as_html
            page_num = e.metadata.page_number
            if page_num in self.html_tag_dict:
                e.text = e.text + f'\n参考图片：\n{self.html_tag_dict[page_num]}\n\n\n'
            documents.append(Document(page_content=e.text, metadata={'page_num': page_num}))
        return documents


if __name__ == '__main__':
    extractor = PptExtractor('test.pptx')
    documents = extractor.extract()
    print(documents)

