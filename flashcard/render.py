"""把记忆卡渲染成可打印的 A4 正反面页面。"""

from __future__ import annotations

import html
from typing import List, Sequence, Tuple

from .model import (
    GROUP_SIZE,
    Card,
    FlashcardError,
    check_flip,
    chunk,
)

PAGE_WIDTH_MM = 210.0
PAGE_HEIGHT_MM = 297.0
CARDS_PER_PAGE = 4
BODY_WIDTH_MM = 74.0
BODY_HEIGHT_MM = 66.0
DEFINITION_SIZES: Tuple[float, ...] = (
    16.0, 14.0, 12.5, 11.0, 10.0, 9.0, 8.0, 7.0, 6.0, 5.5,
)


def _num(value: float) -> str:
    text = "%.1f" % value
    return text.rstrip("0").rstrip(".") if "." in text else text


def _char_width(char: str, font_pt: float) -> float:
    ratio = 0.55 if ord(char) < 128 else 1.0
    return 0.3528 * font_pt * ratio


def wrap_text(text: str, max_width_mm: float, font_pt: float) -> List[str]:
    """按估算宽度逐字折行，中文按一个字宽计算。"""
    if not isinstance(text, str):
        raise FlashcardError("待折行内容必须是文本")
    if max_width_mm <= 0 or font_pt <= 0:
        raise FlashcardError("折行宽度和字号必须大于 0")
    lines: List[str] = []
    current = ""
    width = 0.0
    for char in text:
        size = _char_width(char, font_pt)
        if current and width + size > max_width_mm:
            lines.append(current)
            current = char
            width = size
        else:
            current += char
            width += size
    if current:
        lines.append(current)
    return lines


def term_font_pt(card: Card) -> float:
    """按术语长度估算字号，保证单行放得下。"""
    if not isinstance(card, Card):
        raise FlashcardError("card 必须是 Card 对象")
    length = max(1, len(card.term))
    fit = BODY_WIDTH_MM * 0.9 / (0.3528 * length)
    return round(min(30.0, max(7.0, fit)), 1)


def definition_layout(card: Card) -> Tuple[float, List[str]]:
    """为释义选择最大可用字号，并返回折行结果。"""
    if not isinstance(card, Card):
        raise FlashcardError("card 必须是 Card 对象")
    for size in DEFINITION_SIZES:
        lines = wrap_text(card.definition, BODY_WIDTH_MM, size)
        height = len(lines) * size * 0.3528 * 1.55
        if height <= BODY_HEIGHT_MM:
            return size, lines
    smallest = DEFINITION_SIZES[-1]
    return smallest, wrap_text(card.definition, BODY_WIDTH_MM, smallest)


def render_front_card(card: Card, number: int) -> str:
    """正面：术语居中。"""
    _check_card_number(card, number)
    return (
        '<div class="card front">'
        '<div class="card-head"><span>第 %d 张</span><span>正面</span></div>'
        '<div class="card-body"><div class="term" style="font-size:%spt">%s</div></div>'
        '<div class="card-foot">看术语，想释义</div>'
        "</div>"
        % (number, _num(term_font_pt(card)), html.escape(card.term))
    )


def render_back_card(card: Card, number: int) -> str:
    """背面：释义居中，顶部保留小字术语便于核对。"""
    _check_card_number(card, number)
    size, lines = definition_layout(card)
    body = "<br>".join(html.escape(line) for line in lines)
    return (
        '<div class="card back">'
        '<div class="card-head"><span>第 %d 张</span><span>背面</span></div>'
        '<div class="card-body">'
        '<div class="term-small">%s</div>'
        '<div class="definition" style="font-size:%spt">%s</div>'
        "</div>"
        '<div class="card-foot">对照检查</div>'
        "</div>"
        % (number, html.escape(card.term), _num(size), body)
    )


def _check_card_number(card: Card, number: int) -> None:
    if not isinstance(card, Card):
        raise FlashcardError("card 必须是 Card 对象")
    if isinstance(number, bool) or not isinstance(number, int):
        raise FlashcardError("卡片编号必须是整数")
    if number < 1:
        raise FlashcardError("卡片编号必须从 1 开始")


def _page(
    items: Sequence[Tuple[Card, int]],
    side: str,
    group_no: int,
    page: int,
    total: int,
    title: str,
) -> str:
    blocks: List[str] = []
    for offset in range(CARDS_PER_PAGE):
        if offset < len(items):
            card, number = items[offset]
            if side == "front":
                blocks.append(render_front_card(card, number))
            else:
                blocks.append(render_back_card(card, number))
        else:
            blocks.append('<div class="card blank"></div>')
    head = (
        '<header class="head"><h1>%s</h1>'
        "<span>第 %d 组 · %s · 第 %d / %d 页</span></header>"
        % (
            html.escape(title),
            group_no,
            "正面" if side == "front" else "背面",
            page,
            total,
        )
    )
    note = "看术语，想释义" if side == "front" else "对照释义，检查记忆"
    return (
        '<section class="sheet">%s<div class="cards">%s</div>'
        '<footer class="foot"><span>%s</span><span>flashcard · 零依赖打印工具</span></footer>'
        "</section>" % (head, "".join(blocks), note)
    )


def render_html(
    cards: Sequence[Card],
    title: str = "记忆卡",
    flip: str = "long",
    show_back: bool = True,
) -> str:
    """生成完整 HTML：每 4 张为一组，正面页后紧跟同组背面页。"""
    if not isinstance(cards, (list, tuple)):
        raise FlashcardError("cards 必须是卡片列表")
    if not cards:
        raise FlashcardError("至少需要一张记忆卡")
    for card in cards:
        if not isinstance(card, Card):
            raise FlashcardError("卡片列表里出现了非 Card 对象")
    if not isinstance(title, str) or not title.strip():
        raise FlashcardError("标题不能为空")
    if not isinstance(show_back, bool):
        raise FlashcardError("show_back 必须是布尔值")
    mode = check_flip(flip)

    groups = chunk(cards, GROUP_SIZE)
    pages_per_group = 2 if show_back else 1
    total = len(groups) * pages_per_group
    sheets: List[str] = []
    page = 0
    for group_index, group in enumerate(groups):
        start = group_index * GROUP_SIZE
        front: List[Tuple[Card, int]] = [
            (card, start + offset + 1) for offset, card in enumerate(group)
        ]
        page += 1
        sheets.append(
            _page(front, "front", group_index + 1, page, total, title.strip())
        )
        if not show_back:
            continue
        if mode == "short":
            back = list(front)
        else:
            back = []
            for index in range(0, len(front), 2):
                back.extend(reversed(front[index : index + 2]))
        page += 1
        sheets.append(
            _page(back, "back", group_index + 1, page, total, title.strip())
        )

    toolbar = (
        '<div class="toolbar"><strong>%s</strong>'
        "<span>共 %d 张 · 每组 %d 张 · %s · %s</span></div>"
        % (
            html.escape(title.strip()),
            len(cards),
            GROUP_SIZE,
            "长边翻页" if mode == "long" else "短边翻页",
            "双面打印" if show_back else "仅正面",
        )
    )

    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s\n%s\n</body>\n</html>\n"
        % (html.escape(title.strip()), STYLE, toolbar, "\n".join(sheets))
    )


STYLE = """
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 8mm 0 12mm;
    background: #e2e8f0;
    color: #0f172a;
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  }
  .toolbar {
    width: 210mm;
    margin: 0 auto 6mm;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    color: #334155;
    font-size: 13px;
  }
  .toolbar strong { font-size: 15px; letter-spacing: 1px; }
  .toolbar span { color: #64748b; font-size: 12px; }
  .sheet {
    width: 210mm;
    height: 297mm;
    margin: 0 auto 8mm;
    padding: 13mm 15mm 9mm;
    background: #fff;
    box-shadow: 0 6px 22px rgba(15, 23, 42, 0.14);
    display: flex;
    flex-direction: column;
    page-break-after: always;
    break-after: page;
    overflow: hidden;
  }
  .sheet:last-child { page-break-after: auto; break-after: auto; }
  .head { text-align: center; margin-bottom: 5mm; }
  .head h1 {
    margin: 0 0 1.5mm;
    font-size: 20pt;
    font-weight: 600;
    letter-spacing: 4pt;
  }
  .head span { font-size: 9pt; color: #64748b; letter-spacing: 0.5pt; }
  .cards {
    display: grid;
    grid-template-columns: repeat(2, 87mm);
    grid-template-rows: repeat(2, 100mm);
    gap: 5mm 6mm;
    justify-content: center;
    align-content: start;
  }
  .card {
    border: 0.6mm solid #0f172a;
    border-radius: 2.5mm;
    background: #fff;
    display: flex;
    flex-direction: column;
    padding: 2mm 2.5mm 1.5mm;
    overflow: hidden;
  }
  .card.back { border-color: #0369a1; }
  .card.blank {
    border: 0.25mm dashed #cbd5e1;
    background: #f8fafc;
  }
  .card-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 8pt;
    color: #475569;
    padding: 0 1mm 1mm;
  }
  .card.back .card-head span:last-child { color: #0369a1; }
  .card-body {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 2mm 3mm;
    overflow: hidden;
  }
  .term {
    font-weight: 600;
    letter-spacing: 0.5pt;
    line-height: 1.35;
    overflow-wrap: anywhere;
  }
  .term-small {
    font-size: 8.5pt;
    color: #94a3b8;
    margin-bottom: 2.5mm;
    letter-spacing: 0.5pt;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .definition {
    line-height: 1.55;
    color: #1e293b;
    overflow-wrap: anywhere;
  }
  .card-foot {
    padding: 1.2mm 1mm 0;
    font-size: 7pt;
    color: #94a3b8;
    text-align: center;
  }
  .foot {
    margin-top: auto;
    padding-top: 2.5mm;
    display: flex;
    justify-content: space-between;
    font-size: 8pt;
    color: #94a3b8;
    border-top: 0.2mm solid #e2e8f0;
  }
  @page { size: A4 portrait; margin: 0; }
  @media print {
    body { background: #fff; padding: 0; }
    .toolbar { display: none; }
    .sheet { margin: 0; box-shadow: none; }
    * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
"""
