"""命令行入口单元测试。"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from typing import List

from flashcard.cli import main


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cards = self.root / "cards.csv"
        rows = ["术语,释义"] + ["词语%02d,解释 %02d" % (i, i) for i in range(1, 7)]
        self.cards.write_text("\n".join(rows) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, argv: List[str]) -> int:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            return main(argv)

    def test_generate(self) -> None:
        target = self.root / "cards.html"
        code = self.run_cli(["-i", str(self.cards), "-o", str(target)])
        self.assertEqual(code, 0)
        page = target.read_text(encoding="utf-8")
        self.assertIn("<!doctype html>", page)
        self.assertIn("正面", page)
        self.assertIn("背面", page)

    def test_no_back(self) -> None:
        target = self.root / "front.html"
        code = self.run_cli(["-i", str(self.cards), "-o", str(target), "--no-back"])
        self.assertEqual(code, 0)
        page = target.read_text(encoding="utf-8")
        self.assertNotIn("背面", page)
        self.assertEqual(page.count('<section class="sheet">'), 2)

    def test_flip_short(self) -> None:
        target = self.root / "short.html"
        code = self.run_cli(["-i", str(self.cards), "-o", str(target), "--flip", "short"])
        self.assertEqual(code, 0)
        self.assertIn("短边翻页", target.read_text(encoding="utf-8"))

    def test_invalid_flip(self) -> None:
        target = self.root / "bad.html"
        code = self.run_cli(["-i", str(self.cards), "-o", str(target), "--flip", "diagonal"])
        self.assertEqual(code, 2)
        self.assertFalse(target.exists())

    def test_duplicate_term(self) -> None:
        bad = self.root / "dup.csv"
        bad.write_text("苹果,水果\n苹果,又来了\n", encoding="utf-8")
        code = self.run_cli(["-i", str(bad), "-o", str(self.root / "x.html")])
        self.assertEqual(code, 2)

    def test_missing_file(self) -> None:
        code = self.run_cli(
            ["-i", str(self.root / "missing.csv"), "-o", str(self.root / "x.html")]
        )
        self.assertEqual(code, 1)

    def test_title(self) -> None:
        target = self.root / "t.html"
        code = self.run_cli(
            ["-i", str(self.cards), "-o", str(target), "--title", "英语单词卡"]
        )
        self.assertEqual(code, 0)
        self.assertIn("英语单词卡", target.read_text(encoding="utf-8"))

    def test_missing_input_argument(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with contextlib.redirect_stderr(io.StringIO()):
                main(["-o", str(self.root / "x.html")])
        self.assertEqual(ctx.exception.code, 2)

    def test_help(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_too_long_term(self) -> None:
        bad = self.root / "long.csv"
        bad.write_text("%s,解释\n" % ("字" * 31), encoding="utf-8")
        code = self.run_cli(["-i", str(bad), "-o", str(self.root / "x.html")])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
