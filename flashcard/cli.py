"""命令行入口：生成可打印的双向记忆卡。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from .model import Card, FlashcardError, GROUP_SIZE, load_cards
from .render import CARDS_PER_PAGE, render_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flashcard",
        description="双向记忆卡：术语,释义 CSV 生成 A4 可打印正反面卡片",
    )
    parser.add_argument("--version", action="version", version="flashcard 0.1.0")
    parser.add_argument(
        "-i", "--input", required=True, help="记忆卡 CSV（术语,释义）"
    )
    parser.add_argument(
        "-o", "--output", default="记忆卡.html", help="输出 HTML 路径"
    )
    parser.add_argument(
        "--flip",
        default="long",
        help="双面打印翻页方式：long 长边（默认）或 short 短边",
    )
    parser.add_argument(
        "--no-back", action="store_true", help="只生成正面页"
    )
    parser.add_argument("--title", default="记忆卡", help="页面标题")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        cards: List[Card] = load_cards(args.input)
        page = render_html(
            cards,
            title=args.title,
            flip=args.flip,
            show_back=not args.no_back,
        )
    except FlashcardError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("错误: 读取记忆卡失败: %s" % exc, file=sys.stderr)
        return 1

    try:
        Path(args.output).write_text(page, encoding="utf-8")
    except OSError as exc:
        print("错误: 写入文件失败: %s" % exc, file=sys.stderr)
        return 1

    groups = (len(cards) + GROUP_SIZE - 1) // GROUP_SIZE
    pages = groups * (1 if args.no_back else 2)
    print(
        "已生成 %s：%d 张记忆卡，%d 组，共 %d 页"
        % (args.output, len(cards), groups, pages)
    )
    if args.no_back:
        print("当前只生成正面页；去掉 --no-back 可生成配套背面")
    else:
        print(
            "双面打印请选择「%s翻页」，每页 %d 张，按 Ctrl/Cmd + P 输出"
            % ("长边" if args.flip == "long" else "短边", CARDS_PER_PAGE)
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
