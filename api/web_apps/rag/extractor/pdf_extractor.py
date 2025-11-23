"""Abstract interface for document loader implementations."""
import base64
import os
import tempfile
import time
from typing import Optional
import concurrent
from utils.common_utils import md5
from web_apps.rag.extractor.extractor_base import BaseExtractor
from langchain_core.documents import Document
from utils.storage_utils import storage
import logging
import uuid
from typing import List, Tuple, Dict
import re
from collections import defaultdict
from web_apps.rag.extractor.pdf_utils import extract_pdf_elements, PdfElement, PdfImage
from web_apps.rag.extractor.table_utils import split_to_multi_document_tables, extract_tables_by_chunk_max_token

PDF_READ_RETRY_TIMES = 3
PDF_TABLE_SPLIT_SEP = '------####------'


def cidToChar(cidx):
    return chr(int(re.findall(r'\(cid\:(\d+)\)', cidx)[0]) + 29)


def replace_str_cid(char_str):
    if not "cid:" in char_str:
        return char_str
    res = []
    for x in char_str.split('\n'):
        if x != '' and x != '(cid:3)':  # merely to compact the output
            abc = re.findall(r'\(cid\:\d+\)', x)
            if len(abc) > 0:
                for cid in abc: x = x.replace(cid, cidToChar(cid))
            res.append(repr(x).strip("'"))
        else:
            res.append(x)
    return '\n'.join(res)


def _extract_element_content(el: PdfElement, metadata: dict, ocr_image_text: bool = False, keep_ocr_image: bool = True):
    if el.type == "image":
        image: PdfImage = el.content
        image_name = str(time.time()) + "." + image.ext
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = os.path.abspath(os.path.join(temp_dir, image_name))
            try:
                tmp_bytes = image.image
                with open(image_path, "wb") as img_file:
                    img_file.write(image.image)
                save_file_key = f"{md5(tmp_bytes)}.{image.ext}"
                storage.save(save_file_key, tmp_bytes)
                url = storage.get_download_url(save_file_key)
                html_tag = f'< img src="{url}">'
                if ocr_image_text:
                    with open(image_path, "rb") as f:
                        b_image = f.read()
                        image_base64 = base64.b64encode(b_image).decode("utf-8")
                        ocr_texts = ocr(image_base64)
                        ocr_content = "\n".join(ocr_texts)
                        html_tag = ocr_content + "\n" + html_tag if keep_ocr_image else ocr_content
                return html_tag + '\n'
            except Exception as e:
                f = open(f'o.{image.ext}', 'wb')
                f.write(tmp_bytes)
                logging.error(f"解析pdf图片出错了,{str(e)}")
            return ""

    elif el.type == "table":
        tables = extract_tables_by_chunk_max_token(table_array=el.content,
                                                   table_max_token=1024) + '\n'
        return tables
    else:
        return str(el.content)


def _extract_element_content_dict(el: PdfElement, metadata: dict,
                                  ocr_image_text: bool = False,
                                  keep_ocr_image: bool = True):
    return {el.id_: _extract_element_content(el, metadata, ocr_image_text, keep_ocr_image)}


def _is_page_all_images(elements: List[PdfElement]) -> bool:
    for el in elements:
        if el.type == 'text' and el.content and not el.content.isspace():
            return False
        if el.type == 'table':
            return False
    return True


def _batch_extract_elements_content(elements: List[Tuple[int, List[PdfElement]]],
                                    document_id: str,
                                    file_name: str,
                                    keep_ocr_image: bool = True) -> Dict[str, str]:
    num_workers = 1
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        for page_num, page_elements in elements:
            metadata = {
                "file_name": file_name,
                "document_id": document_id,
                "page_num": page_num,
                "theme_name": file_name
            }
            ocr_page_image = _is_page_all_images(page_elements)
            for _element in page_elements:
                futures.append(executor.submit(_extract_element_content_dict,
                                               el=_element,
                                               metadata=metadata,
                                               ocr_image_text=ocr_page_image,
                                               keep_ocr_image=keep_ocr_image))
    elements_content_map = {}
    for future in concurrent.futures.as_completed(futures):
        elements_content_map.update(future.result())
    return elements_content_map


def ocr(image_base64):
    texts = []
    try:
        # todo ocr识别
        pass
    except Exception as e:
        logging.exception(f"OCR失败，异常.{str(e)}")
    return texts


class PdfExtractor(BaseExtractor):
    """Load pdf files.


    Args:
        file_path: Path to the file to load.
    """

    def __init__(
            self,
            file_path: str,
            file_cache_key: Optional[str] = None,
            return_full_document: Optional[bool] = False,
            optimize_table: Optional[bool] = True,
            table_settings: Dict = None,
            optimize_image: Optional[bool] = False,
            ignore_image_side_less_than: Optional[int] = 0,
            show_progress: Optional[bool] = False,
            keep_ocr_image: Optional[bool] = True,
            extract_image: Optional[bool] = True
    ):
        """Initialize with file path.
        :return_full_document 将文档所有内容合并为一个document展示
        :table_settings pdfplumber表格提取配置
        :optimize_table 表格优化开关(去空行空列、对齐等)
        :optimize_image 图片优化开关
        :ignore_image_side_less_than 图片优化开关开启后，当图片的长宽小于某个长度时，剔除图片
        """
        self._file_path = file_path
        self._file_cache_key = file_cache_key
        self.return_full_document = return_full_document
        self.table_settings = table_settings if table_settings else None
        self.optimize_table = optimize_table
        self.optimize_image = optimize_image
        self.ignore_image_side_less_than = ignore_image_side_less_than
        self.show_progress = show_progress
        self.keep_ocr_image = keep_ocr_image and extract_image
        self.extract_image = extract_image

    @staticmethod
    def _filter_header_footers_by_text(page_group_elements: List[List[PdfElement]],
                                       possible_header_content: list[str],
                                       possible_footer_content: list[str],
                                       ) -> List[List[PdfElement]]:
        common_header = PdfExtractor._common_str(_contents=possible_header_content)
        common_footer = PdfExtractor._common_str(_contents=possible_footer_content)

        if len(page_group_elements) <= 1 or (common_header.isspace() and common_footer.isspace()):
            return page_group_elements

        if not common_header.isspace():
            for group_elements in page_group_elements:
                for _element in group_elements:
                    if _element.type == "text" and not _element.content.isspace():
                        _element.content = _element.content.replace(common_header, "", 1)
        if not common_footer.isspace():
            for group_elements in reversed(page_group_elements):
                for _element in group_elements:
                    if _element.type == "text" and not _element.content.isspace():
                        _element.content = _element.content.replace(common_footer, "", 1)
        return page_group_elements

    @staticmethod
    def _filter_directory_by_coordinate(page_group_elements: List[List[PdfElement]]) -> List[List[PdfElement]]:
        if len(page_group_elements) <= 1:
            return page_group_elements
        count_dict = {}
        pattern = re.compile(r'(\.{20,})\s*\d+$')
        start_index = -1
        for index, page_group_element in enumerate(page_group_elements):
            if index >= 5 or start_index >= 0:
                break
            for _element in page_group_element:
                if start_index >= 0:
                    break
                if _element.type == "text":
                    for content in _element.content.splitlines():
                        if pattern.search(content.rstrip()):
                            count_dict[index] = count_dict.get(index, 0) + 1
                            if count_dict[index] >= 3:
                                start_index = index
                                break
        if start_index >= 0:
            for page_group_element in page_group_elements[start_index:5]:
                for _element in page_group_element:
                    if _element.type == "text":
                        for content in _element.content.splitlines():
                            if pattern.search(content.rstrip()):
                                _element.content = "\n"
        return page_group_elements

    @staticmethod
    def _common_str(_contents: list[str]) -> str:
        if not _contents:
            return ''
            # 将列表中的第一个字符串作为初始比较基准
        common_prefix = _contents[0]
        try:
            for s in _contents:
                if s is None:
                    return ''
                    # 检查当前字符串s是否包含当前的公共前缀
                # 通过迭代缩减公共前缀，直到找到所有字符串都包含的最长前缀
                while not s.startswith(common_prefix):
                    common_prefix = common_prefix[:-1]
                    if not common_prefix:
                        return ''
        except Exception as e:
            return ''
        return common_prefix

    # 通过坐标来去除元素
    @staticmethod
    def filter_header_footers_by_coordinate(page_group_elements: List[List[PdfElement]]) -> List[List[PdfElement]]:
        if len(page_group_elements) <= 3:
            return page_group_elements

        count_map = defaultdict(int)
        # 遍历每个包含Document对象的列表
        for page_elements in page_group_elements:
            # 对于当前列表中的每个Document对象，增加其(text, pos)对的计数
            for page_element in page_elements:
                if page_element.type == 'text':
                    bbox = page_element.bbox
                    count_map[page_element.type + "_ " + "{:.2f}".format(bbox[0]) + "_" + "{:.2f}".format(
                        bbox[1]) + "_" + "{:.2f}".format(
                        bbox[2]) + "_" + "{:.2f}".format(bbox[3]) + "_" + page_element.content] += 1

        _common_datas = [data for data, count in count_map.items()
                         if count > len(page_group_elements) / 3]
        if len(_common_datas) < 1:
            return page_group_elements

        final_page_group_elements: List[List[PdfElement]] = []
        for page_elements in page_group_elements:
            _page_group_elements = []
            for page_element in page_elements:
                _same = False
                for _common_data in _common_datas:
                    if PdfExtractor._same_element(_el=page_element, compare_content=_common_data):
                        _same = True
                        break

                if not _same:
                    _page_group_elements.append(page_element)
            if len(_page_group_elements) > 0:
                final_page_group_elements.append(_page_group_elements)

        # 去除了header和footer元素
        return final_page_group_elements

    @staticmethod
    def _same_element(_el: PdfElement, compare_content: str) -> bool:
        if _el.type != 'text':
            return False
        bbox = _el.bbox
        content = _el.type + "_ " + "{:.2f}".format(bbox[0]) + "_" + "{:.2f}".format(
            bbox[1]) + "_" + "{:.2f}".format(
            bbox[2]) + "_" + "{:.2f}".format(bbox[3]) + "_" + _el.content
        return content == compare_content

    @staticmethod
    # 将表格和图片分割开来，防止后面分割将表给给分到不同chunk
    def _convert_to_documents(_elements: List[PdfElement], metadata: dict) -> List[Document]:
        temp_elements = []
        result: List[Document] = []
        for _element in _elements:
            if _element.type == "image" or _element.type == "table":
                # 优先把文本内容放一起，表格单独开来，否则后没办法拆分了
                if len(temp_elements) > 0:
                    result.append(
                        Document(page_content="".join([el.content for el in temp_elements]), metadata=metadata))
                    temp_elements.clear()

                # 判断表格是否过大需要拆分合并进来
                if PDF_TABLE_SPLIT_SEP in _element.content:
                    result.extend(
                        split_to_multi_document_tables(text='\n' + _element.content + '\n', metadata=metadata))
                    continue
                result.append(Document(page_content=_element.content, metadata=metadata))
            else:
                temp_elements.append(_element)

        if len(temp_elements) > 0:
            result.append(Document(page_content="".join([el.content for el in temp_elements]), metadata=metadata))
        return result

    @staticmethod
    # 寻找第一个文本元素
    def _find_first_text(_elements: List[PdfElement]) -> str:
        for _element in _elements:
            if _element.type == "text" and not _element.content.isspace():
                return _element.content.strip()

    @staticmethod
    def _find_last_text(_elements: List[PdfElement]) -> str:
        for _element in reversed(_elements):
            if _element.type == "text" and not _element.content.isspace():
                return _element.content.strip()

    def extract(self) -> list[Document]:
        document_id = ''
        if not document_id:
            document_id = str(uuid.uuid4())

        docs = []
        _text = ""
        page_group_els = []
        possible_header_content = []
        possible_footer_content = []
        file_name = os.path.basename(self._file_path)
        # 提取pdf元素：页号->元素列表
        logging.info(f"文件[{file_name}]元素解析开始")
        pdf_elements = extract_pdf_elements(self._file_path, self.show_progress,
                                            self.table_settings,
                                            self.optimize_table,
                                            self.optimize_image,
                                            self.ignore_image_side_less_than,
                                            self.extract_image)
        logging.info(f"文件[{file_name}]元素解析完成")
        # 元素内容转换: id->content
        logging.info(f"文件[{file_name}]元素内容提取开始")
        pdf_elements_content_dict = _batch_extract_elements_content(pdf_elements, document_id, file_name,
                                                                    self.keep_ocr_image)
        logging.info(f"文件[{file_name}]元素内容提取完成")

        # 按页面处理头尾
        for page_num, page_elements in pdf_elements:
            _extract_elements = []
            for el in page_elements:
                content = pdf_elements_content_dict.get(el.id_, "")
                if content:
                    _extract_elements.append(PdfElement(el.type, el.bbox, content))
            # 记录下开头和结尾第一个文本,去除页头和页尾
            possible_header_content.append(self._find_first_text(_extract_elements))
            possible_footer_content.append(self._find_last_text(_extract_elements))
            page_group_els.append(_extract_elements)

        logging.info(f"文件[{file_name}]元素头尾去除开始")
        # 根据坐标元素去除内容
        page_group_els = PdfExtractor.filter_header_footers_by_coordinate(page_group_elements=page_group_els)
        page_group_els = PdfExtractor._filter_header_footers_by_text(page_group_elements=page_group_els,
                                                                     possible_footer_content=possible_footer_content,
                                                                     possible_header_content=possible_header_content)
        # 完全依靠规则去除目录信息
        page_group_els = PdfExtractor._filter_directory_by_coordinate(page_group_elements=page_group_els)
        logging.info(f"文件[{self._file_path}]元素头尾去除结束")
        page_num = 0
        metadata = {
            "file_name": file_name,
            "document_id": document_id,
            "page_num": page_num,
            "theme_name": file_name
        }
        for page_els in page_group_els:
            page_num += 1
            metadata["page_num"] = page_num
            if not self.return_full_document:
                docs.extend(PdfExtractor._convert_to_documents(_elements=page_els, metadata=metadata))
            else:
                _text += "".join([_extract_element_content(el, metadata=metadata) for el in page_els])
        if self.return_full_document:
            docs.append(Document(page_content=_text, metadata=metadata))
        return docs


if __name__ == '__main__':
    extractor = PdfExtractor('test.pdf')
    documents = extractor.extract()
    print(documents)
    f = open('out.md', 'w', encoding='utf-8')
    md = '\n\n\n'.join([doc.page_content for doc in documents])
    f.write(md)


