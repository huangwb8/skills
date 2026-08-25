# md-to-word

这个 skill 用来把一个或多个 Markdown 文档转换成可交付的 Word `.docx` 文件，强调模板、美观排版、安全输出和兼容性；它不会修改原始 Markdown，也不会默认覆盖已有输出。

## 用法

### 最推荐用法

```text
请使用 md-to-word skill: `xx.md`
输入：一个或多个 Markdown 文件；可选模板 `default` / `cn-modern` / `compact`
输出：对应的 `.docx` 文件，默认不覆盖已有输出，也不修改原始 Markdown
```

### 进阶用法

```text
请使用 md-to-word skill: `report.md`
输入：`report.md`
输出：`report.docx`
另外，还有下列参数约束：
- 模板：`cn-modern`
- 自动修复 RGBA 图片：是
- 输出目录：`./docx-out`
```

## 能做什么

- 把 Markdown 转成交付级 `.docx`，而不是只调用一次最小 Pandoc 命令。
- 提供内置模板，适合通用、中文友好和紧凑排版三种常见风格。
- 处理 Word 兼容性问题，尤其是图片模式和模板命名空间问题。
- 默认保持输入文件不变，也默认不覆盖已有 docx。
- 不适合编辑现有 Word 文档，也不是通用排版设计器。

## 使用示例

### 示例 1：转换单个 Markdown

```text
请使用 md-to-word skill: `proposal.md`
输入：`proposal.md`
输出：`proposal.docx`
```

### 示例 2：批量转换并指定模板

```text
请使用 md-to-word skill 批量转换这些 Markdown。
输入：`a.md`、`b.md`
输出：对应的 `.docx` 文件
另外，还有下列参数约束：
- 模板：`compact`
- 输出目录：`./out`
```

### 示例 3：强调图片兼容性

```text
请使用 md-to-word skill: `report.md`
输入：`report.md`
输出：`.docx`
另外，还有下列参数约束：
- 自动修复 RGBA 图片：是
- 如果输出已存在：不要覆盖
```

## 输出

- 默认输出为输入文件同目录下的同名 `.docx`。
- 默认不覆盖已有输出。
- 默认不修改、重命名或删除原始 Markdown。
- 开启图片修复时，会在工作目录下创建 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/md-to-word/{yyyy-mm-dd-hh-mm}/` 作为中间工作区。

## 配置

- 配置文件：`md-to-word/config.yaml`
- 内置模板：
  - `default`
  - `cn-modern`
  - `compact`
- 默认模板：`default`
- 允许输入扩展名：`.md`、`.markdown`
- 最大输入数量：`200`

## 备选用法（脚本/硬编码）

如果你明确知道输入文件和模板，脚本方式通常是最稳、最高效的做法。

### 查看模板

```bash
python3 md-to-word/scripts/md_to_word.py --list-templates
```

### 基础转换

```bash
python3 md-to-word/scripts/md_to_word.py proposal.md
```

### 指定模板和输出目录

```bash
python3 md-to-word/scripts/md_to_word.py \
  --template cn-modern \
  --output-dir ./out \
  proposal.md
```

### 修复图片并批量转换

```bash
python3 md-to-word/scripts/md_to_word.py \
  --template compact \
  --fix-images \
  a.md b.md
```

## 常见问题

### Q：它会修改我的 Markdown 吗？

A：不会。这个 skill 的安全边界之一就是“只读取输入 Markdown，输出新的 `.docx`”。

### Q：如果同名 `.docx` 已经存在怎么办？

A：默认会报错并停止，除非你显式使用 `--overwrite`。

### Q：什么时候该用 `--fix-images`？

A：当你的 Markdown 里有 RGBA PNG、透明图或 Word 打开后提示图片兼容性问题时，优先开启它。

### Q：内置模板和自定义 `reference.docx` 怎么选？

A：大多数场景先用内置模板即可；只有你已经有成熟的 Word 样式体系时，再显式传入自定义 `reference.docx`。
