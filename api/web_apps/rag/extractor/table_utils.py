from langchain_core.documents import Document
PDF_TABLE_SPLIT_SEP = '------####------'


def cal_text_token(text: str) -> int:
    # todo: 使用nltk
    return len(text)


def split_to_multi_document_tables(text: str, metadata: dict) -> list[Document]:
    return [Document(page_content='\n' + table_str + '\n', metadata=metadata) for table_str in
            text.split(PDF_TABLE_SPLIT_SEP)]


def _convert_to_html(table: list) -> str:
    # Helper function to convert a 2D list representing a table into an HTML table string.
    html = "<table>"
    for row in table:
        html += "<tr>"
        for cell in row:
            html += f"<td>{cell}</td>"
        html += "</tr>"
    html += "</table>"
    return html


def extract_tables_by_chunk_max_token(table_array: list[list], table_max_token: int) -> str:
    if not table_array:
        return ''

    header, table_data = [table_array[0]], table_array[1:]

    tables = []
    current_table = []
    current_table_token_count = 0

    for row in table_data:
        row_token_count = sum(cal_text_token(str(cell)) for cell in row)
        if current_table_token_count + row_token_count > table_max_token:
            if len(current_table) > 0:
                tables.append(_convert_to_html(header + current_table))
                current_table = []
                current_table_token_count = 0
        current_table.append(row)
        current_table_token_count = current_table_token_count + row_token_count

    if len(current_table) > 0:
        tables.append(_convert_to_html(header + current_table))
    return PDF_TABLE_SPLIT_SEP.join(tables)