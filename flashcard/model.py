"""记忆卡数据模型：CSV 解析、双向翻页顺序与校验。"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union

MAX_TERM = 30
MAX_DEFINITION = 80
GROUP_SIZE = 4

TERM_HEADERS = {"术语", "词条", "正面", "单词"}
DEFINITION_HEADERS = {"释义", "解释", "背面", "含义"}

FLIP_MODES: Tuple[str, ...] = ("long", "short")


class FlashcardError(ValueError):
    """记忆卡数据或参数不合法。"""


@dataclass(frozen=True)
class Card:
    """一张记忆卡：正面术语与背面释义。"""

    term: str
    definition: str

    def __post_init__(self) -> None:
        term = _clean(self.term, "术语")
        definition = _clean(self.definition, "释义")
        if not term:
            raise FlashcardError("术语不能为空")
        if not definition:
            raise FlashcardError("释义不能为空")
        if len(term) > MAX_TERM:
            raise FlashcardError(
                "术语最多 %d 个字符，当前 %d 个：%s"
                % (MAX_TERM, len(term), term)
            )
        if len(definition) > MAX_DEFINITION:
            raise FlashcardError(
                "释义最多 %d 个字符，当前 %d 个" % (MAX_DEFINITION, len(definition))
            )
        object.__setattr__(self, "term", term)
        object.__setattr__(self, "definition", definition)


def _clean(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise FlashcardError("%s必须是文本，当前是 %r" % (label, value))
    return value.strip()


def _decode(data: bytes) -> str:
    if not isinstance(data, (bytes, bytearray)):
        raise FlashcardError("文件内容必须是字节")
    for encoding in ("utf-8-sig", "gbk"):
        try:
            return bytes(data).decode(encoding)
        except UnicodeDecodeError:
            continue
    raise FlashcardError("无法识别文件编码，请另存为 UTF-8 或 GBK 后重试")


def _is_header(cells: Sequence[str]) -> bool:
    if len(cells) < 2:
        return False
    return cells[0] in TERM_HEADERS and cells[1] in DEFINITION_HEADERS


def parse_csv(text: str, source: str = "输入内容") -> List[Card]:
    """解析两列 CSV：术语,释义；表头可选。"""
    if not isinstance(text, str):
        raise FlashcardError("CSV 内容必须是文本")
    text = text.lstrip("\ufeff")
    reader = csv.reader(io.StringIO(text))
    cards: List[Card] = []
    seen: Dict[str, int] = {}
    header_checked = False
    for line_no, row in enumerate(reader, start=1):
        cells = [cell.strip() for cell in row]
        if not any(cells):
            continue
        if not header_checked:
            header_checked = True
            if _is_header(cells):
                continue
        if len(cells) > 2:
            raise FlashcardError(
                "%s 第 %d 行有 %d 列，最多 2 列（术语,释义）"
                % (source, line_no, len(cells))
            )
        term = cells[0] if len(cells) > 0 else ""
        definition = cells[1] if len(cells) > 1 else ""
        if not term:
            raise FlashcardError("%s 第 %d 行缺少术语" % (source, line_no))
        if not definition:
            raise FlashcardError("%s 第 %d 行缺少释义" % (source, line_no))
        if term in seen:
            raise FlashcardError(
                "%s 第 %d 行的术语与第 %d 行重复：%s"
                % (source, line_no, seen[term], term)
            )
        seen[term] = line_no
        try:
            cards.append(Card(term=term, definition=definition))
        except FlashcardError as exc:
            raise FlashcardError("%s 第 %d 行：%s" % (source, line_no, exc)) from exc
    if not cards:
        raise FlashcardError("%s 中没有有效的记忆卡" % source)
    return cards


def load_cards(path: Union[str, Path]) -> List[Card]:
    """读取 CSV 文件并解析。"""
    target = Path(path)
    return parse_csv(_decode(target.read_bytes()), source=str(target))


def check_flip(mode: str) -> str:
    """校验翻页方式：长边翻页或短边翻页。"""
    if not isinstance(mode, str):
        raise FlashcardError("翻页方式必须是文本")
    text = mode.strip().lower()
    if text not in FLIP_MODES:
        raise FlashcardError("翻页方式只能是 long 或 short，当前是 %s" % mode)
    return text


def chunk(cards: Sequence[Card], size: int = GROUP_SIZE) -> List[List[Card]]:
    """把卡片按组切分，用于正面页与背面页配对。"""
    if not isinstance(cards, (list, tuple)) or not cards:
        raise FlashcardError("卡片列表不能为空")
    for card in cards:
        if not isinstance(card, Card):
            raise FlashcardError("卡片列表里出现了非 Card 对象")
    if isinstance(size, bool) or not isinstance(size, int):
        raise FlashcardError("每组张数必须是整数")
    if size < 1:
        raise FlashcardError("每组张数必须大于 0")
    groups: List[List[Card]] = []
    for start in range(0, len(cards), size):
        groups.append(list(cards[start : start + size]))
    return groups


def back_order(group: Sequence[Card], flip: str = "long") -> List[Card]:
    """背面页的卡片顺序：长边翻页左右镜像，短边翻页保持原序。"""
    mode = check_flip(flip)
    if not isinstance(group, (list, tuple)):
        raise FlashcardError("分组必须是卡片列表")
    if not group:
        raise FlashcardError("分组不能为空")
    for card in group:
        if not isinstance(card, Card):
            raise FlashcardError("分组里出现了非 Card 对象")
    items = list(group)
    if mode == "short":
        return items
    ordered: List[Card] = []
    for index in range(0, len(items), 2):
        ordered.extend(reversed(items[index : index + 2]))
    return ordered
