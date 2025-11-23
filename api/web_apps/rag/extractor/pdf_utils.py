import gc
import logging
import pathlib
import uuid
from io import BufferedReader, BytesIO
from typing import List, Union, Tuple, Set
import fitz
import numpy as np
import re
from pdfminer.high_level import extract_text
from pymupdf import Page
from pypdf import PdfReader


def detect_lang(string):
    """
    检查整个字符串是否包含中文
    :param string: 需要检查的字符串
    :return: bool
    """

    for ch in string:
        if u'\u4e00' <= ch <= u'\u9fff':
            return 'zh'
    return 'en'


def detect_pdf_invalid_chars(pdf_file) -> bool:
    """"
    检测PDF中是否包含非法字符
    """

    def _extract_pages(pdf) -> fitz.Document:
        pdf_docs = fitz.open(pdf)
        total_page = len(pdf_docs)
        if total_page == 0:
            # 如果PDF没有页面，直接返回空文档
            return fitz.Document()
        select_page_cnt = min(10, total_page)
        page_num = np.random.choice(total_page, select_page_cnt, replace=False)
        sample_docs = fitz.Document()
        try:
            for index in page_num:
                sample_docs.insert_pdf(pdf_docs, from_page=int(index), to_page=int(index))
        except Exception as e:
            logging.error(str(e))
        return sample_docs

    '''乱码文本用pdfminer提取出来的文本特征是(cid:xxx)'''
    '''pdfminer比较慢,需要先随机抽取10页左右的sample'''
    sample_docs = _extract_pages(pdf_file)
    sample_pdf_bytes = sample_docs.tobytes()
    sample_pdf_file_like_object = BytesIO(sample_pdf_bytes)
    text = extract_text(sample_pdf_file_like_object)
    text = text.replace("\n", "")
    # logger.info(text)
    '''乱码文本用pdfminer提取出来的文本特征是(cid:xxx)'''
    cid_pattern = re.compile(r'\(cid:\d+\)')
    matches = cid_pattern.findall(text)
    cid_count = len(matches)
    cid_len = sum(len(match) for match in matches)
    text_len = len(text)
    if text_len == 0:
        cid_chars_radio = 0
    else:
        cid_chars_radio = cid_count / (cid_count + text_len - cid_len)
    logging.info(f"cid_count: {cid_count}, text_len: {text_len}, cid_chars_radio: {cid_chars_radio}")
    '''当一篇文章存在5%以上的文本是乱码时,认为该文档为乱码文档'''
    if cid_chars_radio > 0.05:
        return True  # 乱码文档
    else:
        return False  # 正常文档


def detect_pdf_invalid_chars2(pdf_file) -> bool:
    """"
    检测PDF中是否包含非法字符
    """
    reader = PdfReader(pdf_file)
    total_page = len(reader.pages)
    select_page_cnt = min(10, total_page)
    page_nums = np.random.choice(total_page, select_page_cnt, replace=False)
    texts = []
    try:
        for page_num in page_nums:
            page = reader.pages[int(page_num)]
            texts.append(page.extract_text())
            page.clear()
    except Exception as ex:
            logging.error(f"pypdf2 read page error.{str(ex)}")
    text = "".join(texts)
    text = text.replace("\n", "")
    # logger.info(text)
    '''乱码文本用pypdf2提取出来的文本特征是/Gxx, xx是两个16进制数字'''
    cid_pattern = re.compile(r'/G[0-9A-F]+')
    matches = cid_pattern.findall(text)
    cid_count = len(matches)
    cid_len = sum(len(match) for match in matches)
    text_len = len(text)
    if text_len == 0:
        cid_chars_radio = 0
    else:
        cid_chars_radio = cid_count / (cid_count + text_len - cid_len)
    logging.info(f"cid_count: {cid_count}, text_len: {text_len}, cid_chars_radio: {cid_chars_radio}")
    '''当一篇文章存在5%以上的文本是乱码时,认为该文档为乱码文档'''
    if cid_chars_radio > 0.05:
        return True  # 乱码文档
    else:
        return False  # 正常文档


class PdfElement:
    def __init__(self, type, bbox, content):
        self.id_ = str(uuid.uuid4())
        self.type = type
        self.bbox = bbox
        self.content = content


class PdfImage:
    def __init__(self, height, width, image, ext):
        self.height = height
        self.width = width
        self.image = image
        self.ext = ext


def _extract_pdf_as_image_elements(pdf_file) -> List[Tuple[int, List[PdfElement]]]:
    results = []
    with fitz.open(pdf_file) as doc:
        total_page = doc.page_count
        for index in range(0, total_page):
            page: Page = doc[index]
            pix = page.get_pixmap(dpi=200, alpha=False)
            element = PdfElement(type='image', bbox=page.rect, content=PdfImage(height=pix.height,
                                                                                width=pix.width,
                                                                                image=pix.tobytes(),
                                                                                ext='png'))
            results.append((index, [element]))
    _release_mypdf_cache()
    return results


def _release_mypdf_cache():
    # 内存回收，避免内存泄漏
    try:
        TOOLS = fitz.TOOLS
    except:
        TOOLS = fitz.Tools()
    if TOOLS:
        TOOLS.store_shrink(100)  # reset MuPDF global context

    from pymupdf.table import CHARS, EDGES
    CHARS.clear()
    EDGES.clear()

    gc.collect()


def extract_pdf_elements(pdf_file: Union[str, pathlib.Path, BufferedReader, BytesIO],
                         show_progress=False,
                         table_settings=None,
                         optimize_table=True,
                         optimize_image=True,
                         ignore_image_side_less_than=50,
                         extract_image=True
                         ) -> List[Tuple[int, List[PdfElement]]]:
    """
    将PDF使用mupdf工具解析成文本、图片、表格
    """
    if detect_pdf_invalid_chars2(pdf_file):
        return _extract_pdf_as_image_elements(pdf_file)
    MAX_PAGES = 300
    MAX_PER_PAGE_ELEMENTS = 300

    results = []

    with fitz.open(pdf_file) as doc:
        total_page = len(doc)
        if total_page > MAX_PAGES:
            raise RuntimeError(f"{pdf_file.name}文件超过了{MAX_PAGES}页")

        for index in range(0, total_page):
            page: Page = doc[index]
            page_blocks = _extract_page_blocks(page, ignore_image_side_less_than, ignore_image_bytes_less_than=1024)
            page_elements = []
            for page_block in page_blocks:
                if page_block["type"] == 0:
                    element = PdfElement("text",
                                         tuple(page_block["bbox"]),
                                         page_block["text"])
                    page_elements.append(element)
                if page_block["type"] == 1:
                    element = PdfElement("image",
                                         tuple(page_block["bbox"]),
                                         PdfImage(height=page_block["height"],
                                                  width=page_block["width"],
                                                  ext=page_block["ext"],
                                                  image=page_block["image"]
                                                  ))
                    page_elements.append(element)
                if page_block["type"] == 2:
                    element = PdfElement("table",
                                         tuple(page_block["bbox"]),
                                         page_block["table"])
                    page_elements.append(element)
            results.append((index, page_elements))

    _release_mypdf_cache()

    return results

def _extract_page_blocks(page: Page,
                         ignore_image_side_less_than=10,
                         ignore_image_bytes_less_than=1024):
    # 1.解析出文本、图片、表格
    # 1.1解析出来的文本和图片的number就是其阅读顺序编号。但是表格不支持一起解析，所以后面要想办法给table也找个number
    text_images = _extract_page_text_and_image_blocks(page, ignore_image_side_less_than, ignore_image_bytes_less_than)
    tables = _extract_page_table_blocks(page)
    # 1.2 图片、文本、表格
    images = [block for block in text_images if block["type"] == 1]
    texts = [block for block in text_images if block["type"] == 0]

    # 2.文本、图片、表格 预处理
    # 2.1.给table加上number(使用文本的number),方便后面排序
    for tb_block in tables:
        for txt_block in texts:
            if txt_block["bbox"] in tb_block["bbox"]:
                tb_block["number"] = txt_block["number"]
                break
    # 2.2.排除表格中的文本
    texts = [block for block in texts if not _box_in_bboxes(block["bbox"], [b["bbox"] for b in tables])]
    # 2.3排除有文字的图片(文字和图片重叠，可能是背景图或者水印图,可以去掉)
    images = [image for image in images if not any([text["bbox"] in image["bbox"] for text in texts])]

    # 3.排序
    # 3.1对文本块进行合并（合并成大的文本块，方便排序）
    texts = _merge_blocks(texts)
    # 3.2排序后，文本和表格的顺序是正确的
    blocks = texts + tables
    blocks.sort(key=lambda b: (b['number'], b["bbox"].y0, b["bbox"].x0))

    if not images:
        return blocks

    # 3.3 区分多列和单列文本算法插入图片到正确位置
    if is_multi_colum_page(texts):
        # 将图片插入到顺序正确的文本和表格中去
        for image in images:
            for i, block in enumerate(blocks):
                if image["bbox"].y0 > block["bbox"].y0:
                    continue
                elif image["bbox"].x0 > block["bbox"].x1:
                    continue
                else:
                    image["number"] = block["number"]
                    break
        for image in images:
            if image["number"] == -1:
                image["number"] = blocks[-1]["number"]
        blocks += images
    else:
        blocks += images
        blocks.sort(key=lambda b: (b["bbox"].y0, b["bbox"].x0))
        _fill_number_by_adjacent_block(blocks)

    # 3.4最后，一起排序(优先按阅读顺序，再遵循线上后下，先左后右)
    blocks.sort(key=lambda b: (b['number'], b["bbox"].y0, b["bbox"].x0))
    return blocks

def is_multi_colum_page(blocks: List):
    """
    判断是否是多列
    当一个block的右边有别的block，那么将该block归于左列。
    所有的左列block占比超过一个阀值，我们认为这是多列的（至少是两列的）
    :param blocks:
    :return:
    """
    if len(blocks) < 2:
        return False
    min_x0 = min([block["bbox"].x0 for block in blocks])
    max_x1 = max([block["bbox"].x1 for block in blocks])

    left_side_blocks = []
    for i in range(0, len(blocks)):
        is_left_block = False
        bboxi_extend_right = fitz.IRect((blocks[i]["bbox"].x0, blocks[i]["bbox"].y0, max_x1, blocks[i]["bbox"].y1))
        for j in range(0, len(blocks)):
            if i == j:
                continue
            bboxj_extend_left = fitz.IRect((min_x0, blocks[j]["bbox"].y0, blocks[j]["bbox"].x1, blocks[j]["bbox"].y1))
            if not (bboxi_extend_right & bboxj_extend_left).is_empty:
                is_left_block = True
                break
        if is_left_block:
            left_side_blocks.append(blocks[i])

    total_area = sum([block["bbox"].get_area() for block in blocks])
    left_area = sum([block["bbox"].get_area() for block in left_side_blocks])
    # 左侧区域占比超过30%
    return left_area / total_area > 0.3


def _fill_number_by_adjacent_block(blocks):
    """
    使用相邻的非-1 number填充block的number
    :param blocks:
    :return:
    """
    n = len(blocks)
    for i in range(n):
        if blocks[i]["number"] == -1:
            # Look for the previous non-negative value
            j = i - 1
            while j >= 0 and blocks[j] == -1:
                j -= 1
            if j >= 0:
                blocks[i]["number"] = blocks[j]["number"]
            else:
                # If no previous non-negative value found, look for the next one
                k = i + 1
                while k < n and blocks[k] == -1:
                    k += 1
                if k < n:
                    blocks[i]["number"] = blocks[k]["number"]
    return blocks


def _box_in_bboxes(bbox, bboxes):
    for box in bboxes:
        if bbox in box:
            return True
    return False


def _box_equal_box(bbox1, bbox2):
    if bbox1 == bbox2:
        return True
    nbbox = bbox1 & bbox2
    if nbbox.is_empty:
        return False
    elif nbbox.get_area() / bbox1.get_area() > 0.95 and nbbox.get_area() / bbox2.get_area() > 0.95:
        return True
    else:
        return False


def _merge_blocks(blocks):
    # 前三个block我们不合并（可能会有页眉、页脚、甚至水印文字。
    # 它们的坐标可能靠中/后位置，但排序在前，如果按照坐标合并，会错误地将它们合并到其他文本中）
    if len(blocks) <= 3:
        return blocks

    _groups: List[Set[int]] = []

    def _add_to_groups(i, j):
        if not _groups:
            _group = set()
            _group.add(i)
            _group.add(j)
            _groups.append(_group)
        else:
            in_groups = False
            for _group in _groups:
                if i in _group or j in _group:
                    in_groups = True
                    _group.add(i)
                    _group.add(j)
                    break
            if not in_groups:
                _group = set()
                _group.add(i)
                _group.add(j)
                _groups.append(_group)

    def _add_to_group(i):
        in_groups = False
        for _group in _groups:
            if i in _group:
                in_groups = True
                break
        if not in_groups:
            _group = set()
            _group.add(i)
            _groups.append(_group)

    for i in range(3, len(blocks)):
        for j in range(4, len(blocks)):
            blocki = blocks[i]
            blockj = blocks[j]

            # 两个block有交叉，就进行合并
            thrshold = min(3, int(min(blocki["line_height"], blockj["line_height"]) * 0.3))
            # 适当扩展下高度进行比较
            if (not (blocki["bbox"] & blockj["bbox"]).is_empty or
                    not ((blocki["bbox"] + [0, 0, 0, thrshold]) & (blockj["bbox"] + [0, 0, 0, thrshold])).is_empty):
                _add_to_groups(i, j)
                nbbox = fitz.EMPTY_IRECT()
                nbbox |= blocki["bbox"]
                nbbox |= blockj["bbox"]
                blocki["bbox"] = blockj["bbox"] = nbbox
                blocki["number"] = blocki["number"] = min(blocki["number"], blockj["number"])

    for i in range(0, len(blocks)):
        _add_to_group(i)

    nblocks = []
    for _group in _groups:
        lst = list(_group)
        lst.sort()
        nblock = blocks[lst[0]]
        nblock["text"] = "".join([blocks[i]["text"] for i in lst])
        nblocks.append(nblock)
    return nblocks


def _optimize_table_content(table: List[List[str]]):
    '''
    表格优化：
    1、单行或单列表格，不作为表格展示；
    2、表格中全部为空白的行或者列剔除掉；
    3、对表格列进行对齐
    :param table:
    :return:
    '''
    # 1、剔除全部未空白的行和列
    useful_column_index = set()
    unuseful_row_index = set()
    for _rindex, _row in enumerate(table):
        row = [col for col in _row if col is not None and col.strip() != '']
        if len(row) == 0:
            unuseful_row_index.add(_rindex)
            continue
        for _cindex, _column in enumerate(_row):
            if _column is not None and _column.strip() != '':
                useful_column_index.add(_cindex)

    new_table = []
    # 2、单行或单列表格，直接返回空，不再作为表格展示
    if len(unuseful_row_index) >= len(table) - 1 or len(useful_column_index) <= 1:
        return new_table

    # 表格重组
    for _rindex, _row in enumerate(table):
        if _rindex in unuseful_row_index:
            continue
        new_row = []
        for _cindex, _column in enumerate(_row):
            if _cindex not in useful_column_index:
                continue
            new_row.append(_column.strip() if _column is not None else '')
        new_table.append(new_row)

    # 3、列重新对齐
    # 因为原理是根据边框识别的table，可能会存在列错位。
    # 比如本来都是两列的表格，错位成了三列（第一行1，3列有内容，第二行2，3列，第三行是1，2列）。
    # 我们判断所有行有意义的列都等于某个数字时，就把列数当成这个数字，对列进行重新对齐
    _first_row_len = len([col for col in new_table[0] if col != ''])
    _all_row_len_equals_first = True
    for row in new_table:
        _cnt = sum(1 for col in row if col != '')
        if _cnt != _first_row_len:
            _all_row_len_equals_first = False
            break
    if _all_row_len_equals_first:
        new_table = [[col for col in row if col != ''] for row in new_table]

    return new_table


def _extract_page_text_and_image_blocks(page: Page,
                                        ignore_image_side_less_than=10,
                                        ignore_image_bytes_less_than=100):
    """
    解析文本和图片，同时解析这两个是为了利用mupdf的自动按照pdf原始顺序排序，排序后会带有number字段作为顺序
    """
    blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT | fitz.TEXT_PRESERVE_IMAGES)["blocks"]
    text_image_blocks = []

    for b in blocks:
        # 只保留文本和图片的block
        bbox = fitz.IRect(b["bbox"])  # bbox of the block
        # 文本
        if b["type"] == 0 and b['lines']:
            # 只取水平文字
            line0 = b["lines"][0]  # get first line
            if line0["dir"] != (1, 0):  # only accept horizontal text
                continue

            line_texts = []
            srect = fitz.EMPTY_IRECT()
            for line in b["lines"]:
                line_text = "".join([s["text"].strip() for s in line["spans"]])
                line_lang = detect_lang(line_text)
                if len(line_text) > 0:
                    srect |= fitz.IRect(line["bbox"])
                # 遇到一些一个字一个span的文档，这种单字语言判断不准，需要用整行文本判断。然后英文要加空格，中文不用
                line_text = ("" if "zh" in line_lang else " ").join([s["text"].strip() for s in line["spans"]])
                line_texts.append(line_text)
            bbox = +srect
            if bbox.is_empty:
                continue

            block_lang = detect_lang("".join(line_texts))
            block_text = ("" if "zh" in block_lang else " ").join(line_texts)
            block_text = block_text.strip().replace("\n", "")
            block_text += "\n"
            b["text"] = block_text
            b["line_height"] = round(min([line["bbox"][3] - line["bbox"][1] for line in b["lines"]]))
            del b["lines"]
        elif b["type"] == 1:  # 图片
            if b["height"] < ignore_image_side_less_than or (bbox.y1 - bbox.y0) < ignore_image_side_less_than:
                continue
            if b["width"] < ignore_image_side_less_than or (bbox.x1 - bbox.x0) < ignore_image_side_less_than:
                continue
            if b["ext"] not in ["png", "jpg", "jpeg"]:
                continue
            if b["size"] < ignore_image_bytes_less_than:
                continue
            b["number"] = -1
        # bbox转成IRect,方便后续操作
        b["bbox"] = bbox

        if not bbox.is_empty:
            text_image_blocks.append(b)
    return text_image_blocks


def _extract_page_table_blocks(page: Page):
    # 找到所有表格
    _tables = []
    try:
        tabs = page.find_tables(strategy='lines_strict')
        if tabs.tables:
            for tab in tabs:
                _tables.append((tab.bbox, tab.extract()))
    except Exception as e:
        logging.error(f"extract page table error:page_no={page.number}.")
        raise e

    # 排除只有一行或者一列的表格
    _tables_bbox = [table[0] for table in _tables if
                    len(table[1]) > 1 and all([True if len(row) > 1 else False for row in table[1]])]
    _tables_data = [table[1] for table in _tables if
                    len(table[1]) > 1 and all([True if len(row) > 1 else False for row in table[1]])]

    table_blocks = []

    # 对表格再进行对齐优化
    for i, table_bbox in enumerate(_tables_bbox):
        table_data = _optimize_table_content(_tables_data[i])
        if not table_data:
            continue
        if len(table_data) <= 1:
            continue
        if not all([True if len(row) > 1 else False for row in table_data]):
            continue
        table_blocks.append({
            "bbox": fitz.IRect(table_bbox),
            "table": table_data,
            "type": 2,
            "number": -1
        })
    return table_blocks


def _extract_page_text_and_image_blocks(page: Page,
                                        ignore_image_side_less_than=10,
                                        ignore_image_bytes_less_than=100):
    """
    解析文本和图片，同时解析这两个是为了利用mupdf的自动按照pdf原始顺序排序，排序后会带有number字段作为顺序
    """
    blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT | fitz.TEXT_PRESERVE_IMAGES)["blocks"]
    text_image_blocks = []

    for b in blocks:
        # 只保留文本和图片的block
        bbox = fitz.IRect(b["bbox"])  # bbox of the block
        # 文本
        if b["type"] == 0 and b['lines']:
            # 只取水平文字
            line0 = b["lines"][0]  # get first line
            if line0["dir"] != (1, 0):  # only accept horizontal text
                continue

            line_texts = []
            srect = fitz.EMPTY_IRECT()
            for line in b["lines"]:
                line_text = "".join([s["text"].strip() for s in line["spans"]])
                line_lang = detect_lang(line_text)
                if len(line_text) > 0:
                    srect |= fitz.IRect(line["bbox"])
                # 遇到一些一个字一个span的文档，这种单字语言判断不准，需要用整行文本判断。然后英文要加空格，中文不用
                line_text = ("" if "zh" in line_lang else " ").join([s["text"].strip() for s in line["spans"]])
                line_texts.append(line_text)
            bbox = +srect
            if bbox.is_empty:
                continue

            block_lang = detect_lang("".join(line_texts))
            block_text = ("" if "zh" in block_lang else " ").join(line_texts)
            block_text = block_text.strip().replace("\n", "")
            block_text += "\n"
            b["text"] = block_text
            b["line_height"] = round(min([line["bbox"][3] - line["bbox"][1] for line in b["lines"]]))
            del b["lines"]
        elif b["type"] == 1:  # 图片
            if b["height"] < ignore_image_side_less_than or (bbox.y1 - bbox.y0) < ignore_image_side_less_than:
                continue
            if b["width"] < ignore_image_side_less_than or (bbox.x1 - bbox.x0) < ignore_image_side_less_than:
                continue
            if b["ext"] not in ["png", "jpg", "jpeg"]:
                continue
            if b["size"] < ignore_image_bytes_less_than:
                continue
            b["number"] = -1
        # bbox转成IRect,方便后续操作
        b["bbox"] = bbox

        if not bbox.is_empty:
            text_image_blocks.append(b)
    return text_image_blocks
