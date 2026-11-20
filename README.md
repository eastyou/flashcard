# flashcard

[![CI](https://github.com/eastyou/flashcard/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/flashcard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

给学生用的双向记忆卡生成器：把「术语,释义」整理成 CSV，一条命令生成 A4 可打印的正反面卡片。**零依赖，不联网，打印即用。**

每页 2×2 四张，每 4 张为一组：先印正面（看术语想释义），紧接着印同组背面（对照检查）。支持长边 / 短边两种翻页方式，双面打印后裁开就能用。

## 特性

- **正反面配对**：每 4 张一组，正面页后紧跟同组背面页，不会错位
- **翻页方式可选**：`--flip long` 长边翻页（左右镜像 1↔2、3↔4），`--flip short` 短边翻页（保持原序）
- **只印正面**：`--no-back` 生成单面卡片，适合课堂快速问答
- **字号自适应**：术语按长度缩放，释义自动折行并选择最大可用字号
- **一页四张**：A4 纵向 2×2，带卡片编号与正反面标记
- **表头可选**：`术语,释义`、`词条,解释`、`正面,背面`、`单词,含义` 都能识别
- **逐行校验**：空术语、空释义、超长内容、多余列、重复术语都会指出具体行号
- **编码兼容**：UTF-8（含 BOM）与 GBK 自动识别，Excel 导出的 CSV 可直接用
- **78 个单元测试**：覆盖 CSV 解析、编码识别、分组、翻页顺序、排版与命令行

## 安装

```bash
pip install flashcard
```

也可以直接下载源码，在项目目录里运行：

```bash
python -m flashcard --help
```

## 用法

准备 `记忆卡.csv`：

```csv
术语,释义
photosynthesis,光合作用：绿色植物利用光能把二氧化碳和水合成有机物并释放氧气
gravity,重力：地球对物体向下的吸引力
```

生成双面记忆卡：

```bash
python -m flashcard -i 记忆卡.csv -o 记忆卡.html
```

只印正面，使用短边翻页：

```bash
python -m flashcard -i 记忆卡.csv --no-back --flip short
```

### 参数

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `-i, --input` | 记忆卡 CSV（术语,释义） | 必填 |
| `-o, --output` | 输出 HTML 路径 | `记忆卡.html` |
| `--flip` | 双面打印翻页方式：`long` 长边 / `short` 短边 | `long` |
| `--no-back` | 只生成正面页 | 关闭 |
| `--title` | 页面标题 | `记忆卡` |

### CSV 格式

两列，第一列术语，第二列释义：

```csv
术语,释义
苹果,一种常见的水果
香蕉,一种热带水果
```

- 表头可有可无，支持 `术语/释义`、`词条/解释`、`正面/背面`、`单词/含义`
- 术语最多 30 个字符，释义最多 80 个字符
- 术语不能重复，重复会指出两次出现的行号
- 编码支持 UTF-8（含 BOM）与 GBK

## 打印

用浏览器打开生成的 HTML，按 `Ctrl/Cmd + P`：

- 纸张：A4 纵向
- 双面：勾选「双面打印」，翻页方式与 `--flip` 保持一致
  - `long`：沿长边翻页（像翻书）
  - `short`：沿短边翻页（像翻日历）
- 边距：无 / 默认
- 勾选「背景图形」，卡片边框才会打印

印好后沿卡片边框裁开即可。建议先用 4 张卡片试印，确认正反面方向无误再批量打印。

## 项目结构

```text
flashcard/
├── flashcard/
│   ├── model.py    # CSV 解析、分组与翻页顺序
│   ├── render.py   # 正反面卡片排版与字号自适应
│   └── cli.py      # 命令行入口
├── tests/          # 78 个单元测试
└── examples/       # 示例记忆卡
```

## 开发

```bash
python -m unittest discover -s tests
```

## 许可证

[MIT](LICENSE) © 2026 eastyou
