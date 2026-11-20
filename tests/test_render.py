"""render 模块单元测试。"""

from __future__ import annotations

import unittest
from typing import List

from flashcard.model import Card, FlashcardError
from flashcard.render import (
    CARDS_PER_PAGE,
    definition_layout,
    render_back_card,
    render_front_card,
    render_html,
    term_font_pt,
    wrap_text,
)


def make_cards(count: int) -> List[Card]:
    terms = ["苹果", "香蕉", "西瓜", "葡萄", "草莓", "柠檬"]
    return [
        Card(term=terms[index % len(terms)], definition="解释 %d" % (index + 1))
        for index in range(count)
    ]


class RenderCardTest(unittest.TestCase):
    def test_front(self) -> None:
        markup = render_front_card(Card("苹果", "一种水果"), 1)
        self.assertIn('<div class="card front">', markup)
        self.assertIn("第 1 张", markup)
        self.assertIn("正面", markup)
        self.assertIn("苹果", markup)

    def test_back(self) -> None:
        markup = render_back_card(Card("苹果", "一种水果"), 2)
        self.assertIn('<div class="card back">', markup)
        self.assertIn("背面", markup)
        self.assertIn("一种水果", markup)
        self.assertIn("苹果", markup)

    def test_front_bad_number(self) -> None:
        for value in (0, -1, True, "1"):
            with self.assertRaises(FlashcardError):
                render_front_card(Card("苹果", "水果"), value)  # type: ignore[arg-type]

    def test_back_non_card(self) -> None:
        with self.assertRaises(FlashcardError):
            render_back_card("苹果", 1)  # type: ignore[arg-type]

    def test_escape(self) -> None:
        markup = render_front_card(Card("<苹果>", "水果"), 1)
        self.assertIn("&lt;苹果&gt;", markup)


class RenderHtmlTest(unittest.TestCase):
    def test_four_cards_two_pages(self) -> None:
        page = render_html(make_cards(4))
        self.assertEqual(page.count('<section class="sheet">'), 2)
        self.assertIn("正面", page)
        self.assertIn("背面", page)
        self.assertIn("A4 portrait", page)

    def test_two_groups(self) -> None:
        page = render_html(make_cards(8))
        self.assertEqual(page.count('<section class="sheet">'), 4)

    def test_partial_group_blanks(self) -> None:
        page = render_html(make_cards(5))
        self.assertEqual(page.count('<section class="sheet">'), 4)
        self.assertEqual(page.count('<div class="card blank">'), 6)

    def test_no_back(self) -> None:
        page = render_html(make_cards(8), show_back=False)
        self.assertEqual(page.count('<section class="sheet">'), 2)
        self.assertNotIn("背面", page)

    def test_long_flip_order(self) -> None:
        cards = [
            Card("甲", "一"), Card("乙", "二"), Card("丙", "三"), Card("丁", "四"),
        ]
        parts = render_html(cards, flip="long").split('<section class="sheet">')
        back = parts[2]
        self.assertLess(back.index(">乙</div>"), back.index(">甲</div>"))
        self.assertLess(back.index(">丁</div>"), back.index(">丙</div>"))
        self.assertIn("第 2 张", back)

    def test_short_flip_order(self) -> None:
        cards = [
            Card("甲", "一"), Card("乙", "二"), Card("丙", "三"), Card("丁", "四"),
        ]
        parts = render_html(cards, flip="short").split('<section class="sheet">')
        back = parts[2]
        self.assertLess(back.index(">甲</div>"), back.index(">乙</div>"))
        self.assertLess(back.index(">丙</div>"), back.index(">丁</div>"))

    def test_numbers(self) -> None:
        page = render_html(make_cards(6), show_back=False)
        for number in range(1, 7):
            self.assertIn("第 %d 张" % number, page)

    def test_title_escaped(self) -> None:
        page = render_html(make_cards(4), title="<记忆卡>")
        self.assertIn("&lt;记忆卡&gt;", page)

    def test_empty_cards(self) -> None:
        with self.assertRaises(FlashcardError):
            render_html([])

    def test_non_sequence(self) -> None:
        with self.assertRaises(FlashcardError):
            render_html("cards")  # type: ignore[arg-type]

    def test_non_card(self) -> None:
        with self.assertRaises(FlashcardError):
            render_html(["card"])  # type: ignore[list-item]

    def test_empty_title(self) -> None:
        with self.assertRaises(FlashcardError):
            render_html(make_cards(4), title=" ")

    def test_bad_show_back(self) -> None:
        with self.assertRaises(FlashcardError):
            render_html(make_cards(4), show_back=1)  # type: ignore[arg-type]

    def test_bad_flip(self) -> None:
        with self.assertRaises(FlashcardError):
            render_html(make_cards(4), flip="diagonal")

    def test_toolbar_text(self) -> None:
        page = render_html(make_cards(4), flip="short")
        self.assertIn("短边翻页", page)
        self.assertIn("双面打印", page)

    def test_cards_per_page(self) -> None:
        self.assertEqual(CARDS_PER_PAGE, 4)


class LayoutTest(unittest.TestCase):
    def test_term_font_bounds(self) -> None:
        size = term_font_pt(Card("苹果", "水果"))
        self.assertGreaterEqual(size, 7.0)
        self.assertLessEqual(size, 30.0)

    def test_long_term_smaller(self) -> None:
        short = term_font_pt(Card("苹果", "水果"))
        long = term_font_pt(Card("字" * 30, "水果"))
        self.assertLess(long, short)

    def test_definition_layout(self) -> None:
        size, lines = definition_layout(Card("苹果", "一种常见的水果，富含维生素。"))
        self.assertGreater(size, 0)
        self.assertEqual("".join(lines), "一种常见的水果，富含维生素。")

    def test_long_definition_wraps(self) -> None:
        size, lines = definition_layout(Card("苹果", "字" * 80))
        self.assertGreater(len(lines), 1)
        self.assertLessEqual(size, 16.0)

    def test_wrap_text_non_text(self) -> None:
        with self.assertRaises(FlashcardError):
            wrap_text(1, 70.0, 10.0)  # type: ignore[arg-type]

    def test_wrap_text_zero_width(self) -> None:
        with self.assertRaises(FlashcardError):
            wrap_text("苹果", 0, 10.0)

    def test_wrap_text_zero_font(self) -> None:
        with self.assertRaises(FlashcardError):
            wrap_text("苹果", 70.0, 0)

    def test_wrap_ascii_more_per_line(self) -> None:
        chinese = wrap_text("字" * 12, 40.0, 10.0)
        english = wrap_text("a" * 12, 40.0, 10.0)
        self.assertGreater(len(chinese), len(english))


if __name__ == "__main__":
    unittest.main()
