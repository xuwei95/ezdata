"""
递归字符切分 —— 紧凑实现 master 的 RecursiveCharacterTextSplitter 行为,不引 langchain。

按分隔符优先级递归切(段落→行→句→词→字),尽量在自然边界断开,块间保留 overlap 字符。
中英文标点都纳入分隔符。chunk_size / chunk_overlap 走文档级 chunk_strategy。
"""

from __future__ import annotations

# 分隔符优先级:从"大"到"小"
_SEPARATORS = ['\n\n', '\n', '。', '！', '？', '. ', '! ', '? ', '；', '; ', '，', ', ', ' ', '']


def _split_by(text: str, sep: str) -> list[str]:
    if sep == '':
        return list(text)
    parts = text.split(sep)
    # 保留分隔符附着在前段尾部(除最后一段),更贴近自然语义
    return [p + sep for p in parts[:-1]] + parts[-1:] if len(parts) > 1 else parts


def _recursive(text: str, size: int, seps: list[str]) -> list[str]:
    if len(text) <= size or not seps:
        return [text] if text else []
    sep, rest = seps[0], seps[1:]
    chunks: list[str] = []
    buf = ''
    for piece in _split_by(text, sep):
        if len(piece) > size:
            if buf:
                chunks.append(buf)
                buf = ''
            chunks.extend(_recursive(piece, size, rest))  # 该片仍超长,降级再切
        elif len(buf) + len(piece) <= size:
            buf += piece
        else:
            if buf:
                chunks.append(buf)
            buf = piece
    if buf:
        chunks.append(buf)
    return chunks


def split_text(text: str, chunk_size: int = 1024, chunk_overlap: int = 200) -> list[str]:
    """切分并在相邻块间补 overlap。返回非空、strip 后的块列表。"""
    text = (text or '').strip()
    if not text:
        return []
    chunk_overlap = max(0, min(chunk_overlap, chunk_size // 2))
    raw = _recursive(text, chunk_size, _SEPARATORS)
    raw = [c.strip() for c in raw if c.strip()]
    if chunk_overlap == 0 or len(raw) <= 1:
        return raw
    out = [raw[0]]
    for cur in raw[1:]:
        prev = out[-1]
        tail = prev[-chunk_overlap:]
        out.append((tail + cur)[:chunk_size + chunk_overlap])
    return out
