"""model 模块单元测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import List

from flashcard.model import (
    MAX_DEFINITION,
    MAX_TERM,
    Card,
    FlashcardError,
    back_order,
    check_flip,
    chunk,
    load_cards,
    parse_csv,
)


def make_cards(count: int) -> List[Card]:
    return [
        Card(term="术语%02d" % index, definition="释义 %02d" % index)
        for index in range(1, count + 1)
    ]


class ParseCsvTest(unittest.TestCase):
    def test_without_header(self) -> None:
        cards = parse_csv("苹果,一种水果\n香蕉,一种水果\n")
        self.assertEqual([card.term for card in cards], ["苹果", "香蕉"])

    def test_header_term_definition(self) -> None:
        cards = parse_csv("术语,释义\n苹果,一种水果\n")
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].term, "苹果")

    def test_header_variants(self) -> None:
        for header in ("词条,解释", "正面,背面", "单词,含义"):
            cards = parse_csv(header + "\n苹果,水果\n")
            self.assertEqual(len(cards), 1, header)

    def test_non_header_first_row(self) -> None:
        cards = parse_csv("术语,说明\n苹果,水果\n")
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0].term, "术语")

    def test_extra_column(self) -> None:
        with self.assertRaises(FlashcardError) as ctx:
            parse_csv("苹果,水果,备注\n")
        self.assertIn("第 1 行", str(ctx.exception))
        self.assertIn("最多 2 列", str(ctx.exception))

    def test_missing_definition(self) -> None:
        with self.assertRaises(FlashcardError) as ctx:
            parse_csv("苹果\n")
        self.assertIn("第 1 行", str(ctx.exception))

    def test_missing_term(self) -> None:
        with self.assertRaises(FlashcardError) as ctx:
            parse_csv(",水果\n")
        self.assertIn("第 1 行", str(ctx.exception))

    def test_duplicate_term(self) -> None:
        with self.assertRaises(FlashcardError) as ctx:
            parse_csv("苹果,水果\n香蕉,水果\n苹果,又来了\n")
        self.assertIn("第 3 行", str(ctx.exception))
        self.assertIn("第 1 行", str(ctx.exception))

    def test_bom(self) -> None:
        cards = parse_csv("\ufeff苹果,水果\n")
        self.assertEqual(cards[0].term, "苹果")

    def test_trim_spaces(self) -> None:
        cards = parse_csv("  苹果  ,  水果  \n")
        self.assertEqual(cards[0].term, "苹果")
        self.assertEqual(cards[0].definition, "水果")

    def test_empty_text(self) -> None:
        with self.assertRaises(FlashcardError):
            parse_csv("\n\n")

    def test_non_text(self) -> None:
        with self.assertRaises(FlashcardError):
            parse_csv(123)  # type: ignore[arg-type]

    def test_term_too_long(self) -> None:
        with self.assertRaises(FlashcardError) as ctx:
            parse_csv("%s,释义\n" % ("字" * (MAX_TERM + 1)))
        self.assertIn("第 1 行", str(ctx.exception))

    def test_definition_too_long(self) -> None:
        with self.assertRaises(FlashcardError):
            parse_csv("苹果,%s\n" % ("字" * (MAX_DEFINITION + 1)))

    def test_load_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cards.csv"
            path.write_text("苹果,水果\n", encoding="utf-8")
            self.assertEqual(load_cards(path)[0].definition, "水果")

    def test_load_gbk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cards.csv"
            path.write_bytes("苹果,水果\n".encode("gbk"))
            self.assertEqual(load_cards(path)[0].term, "苹果")

    def test_unknown_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cards.csv"
            path.write_bytes(b"\xff\xff\xff")
            with self.assertRaises(FlashcardError):
                load_cards(path)

    def test_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_cards("/tmp/definitely-missing-flashcard.csv")


class CardTest(unittest.TestCase):
    def test_empty_term(self) -> None:
        with self.assertRaises(FlashcardError):
            Card(term="  ", definition="水果")

    def test_empty_definition(self) -> None:
        with self.assertRaises(FlashcardError):
            Card(term="苹果", definition="")

    def test_non_text(self) -> None:
        with self.assertRaises(FlashcardError):
            Card(term=1, definition="水果")  # type: ignore[arg-type]

    def test_trim(self) -> None:
        card = Card(term=" 苹果 ", definition=" 水果 ")
        self.assertEqual(card.term, "苹果")
        self.assertEqual(card.definition, "水果")


class ChunkTest(unittest.TestCase):
    def test_full_group(self) -> None:
        groups = chunk(make_cards(8))
        self.assertEqual(len(groups), 2)
        self.assertEqual([len(group) for group in groups], [4, 4])

    def test_partial_group(self) -> None:
        groups = chunk(make_cards(6))
        self.assertEqual([len(group) for group in groups], [4, 2])

    def test_empty(self) -> None:
        with self.assertRaises(FlashcardError):
            chunk([])

    def test_non_sequence(self) -> None:
        with self.assertRaises(FlashcardError):
            chunk("cards")  # type: ignore[arg-type]

    def test_non_card(self) -> None:
        with self.assertRaises(FlashcardError):
            chunk(["card"])  # type: ignore[list-item]

    def test_bad_size(self) -> None:
        with self.assertRaises(FlashcardError):
            chunk(make_cards(4), size=0)

    def test_bool_size(self) -> None:
        with self.assertRaises(FlashcardError):
            chunk(make_cards(4), size=True)  # type: ignore[arg-type]


class BackOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cards = make_cards(4)

    def test_long_mirrors_pairs(self) -> None:
        ordered = back_order(self.cards, "long")
        self.assertEqual([card.term for card in ordered], ["术语02", "术语01", "术语04", "术语03"])

    def test_long_partial(self) -> None:
        ordered = back_order(make_cards(3), "long")
        self.assertEqual([card.term for card in ordered], ["术语02", "术语01", "术语03"])

    def test_short_keeps_order(self) -> None:
        ordered = back_order(self.cards, "short")
        self.assertEqual([card.term for card in ordered], [card.term for card in self.cards])

    def test_empty(self) -> None:
        with self.assertRaises(FlashcardError):
            back_order([], "long")

    def test_non_sequence(self) -> None:
        with self.assertRaises(FlashcardError):
            back_order("card", "long")  # type: ignore[arg-type]

    def test_non_card(self) -> None:
        with self.assertRaises(FlashcardError):
            back_order(["card"], "long")  # type: ignore[list-item]

    def test_bad_mode(self) -> None:
        with self.assertRaises(FlashcardError):
            back_order(self.cards, "diagonal")


class FlipTest(unittest.TestCase):
    def test_valid(self) -> None:
        self.assertEqual(check_flip("long"), "long")
        self.assertEqual(check_flip(" SHORT "), "short")

    def test_invalid(self) -> None:
        with self.assertRaises(FlashcardError):
            check_flip("vertical")

    def test_non_text(self) -> None:
        with self.assertRaises(FlashcardError):
            check_flip(1)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
