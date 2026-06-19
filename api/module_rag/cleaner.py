"""文本清洗 —— 移植 master CleanProcessor,默认规则开启。"""

from __future__ import annotations

import re


def clean_text(text: str, *, remove_extra_spaces: bool = True, remove_urls_emails: bool = False) -> str:
    if not text:
        return ''
    # 去非法符号
    text = re.sub(r'<\|', '<', text)
    text = re.sub(r'\|>', '>', text)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\xEF\xBF\xBE]', '', text)
    text = re.sub('￾', '', text)
    if remove_extra_spaces:
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[\t\f\r\x20  ᠎ -   　]{2,}', ' ', text)
    if remove_urls_emails:
        text = re.sub(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', '', text)
        text = re.sub(r'https?://[^\s]+', '', text)
    return text.strip()
