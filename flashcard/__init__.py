"""flashcard：A4 可打印双向记忆卡。"""

from __future__ import annotations

from .model import (
    DEFINITION_HEADERS,
    FLIP_MODES,
    GROUP_SIZE,
    MAX_DEFINITION,
    MAX_TERM,
    TERM_HEADERS,
    Card,
    FlashcardError,
    back_order,
    check_flip,
    chunk,
    load_cards,
    parse_csv,
)
from .render import (
    CARDS_PER_PAGE,
    definition_layout,
    render_back_card,
    render_front_card,
    render_html,
    term_font_pt,
    wrap_text,
)

__version__ = "0.1.0"

__all__ = [
    "CARDS_PER_PAGE",
    "DEFINITION_HEADERS",
    "FLIP_MODES",
    "GROUP_SIZE",
    "MAX_DEFINITION",
    "MAX_TERM",
    "TERM_HEADERS",
    "Card",
    "FlashcardError",
    "back_order",
    "check_flip",
    "chunk",
    "definition_layout",
    "load_cards",
    "parse_csv",
    "render_back_card",
    "render_front_card",
    "render_html",
    "term_font_pt",
    "wrap_text",
    "__version__",
]
