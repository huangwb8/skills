# Any Picture Format

这个 skill 用来把图片转换成你需要的目标格式，适合单文件、批量目录、URL 图片和剪贴板图片的格式转换；如果你只是想裁剪、缩放或查看图片信息，就不该用它。

## 用法

### 最推荐用法

```text
请使用 any-picture-format skill 将图片格式转换为目标格式。
输入：`/path/to/image.png` 或图片 URL 或剪贴板图片；目标格式如 `jpeg` / `png` / `webp`
输出：转换后的图片文件，默认保留原文件并生成新文件
```

### 进阶用法

```text
请使用 any-picture-format skill 批量转换一个目录里的图片。
输入：图片目录 `/path/to/images`；目标格式 `webp`
输出：批量转换后的图片文件
另外，还有下列参数约束：
- 递归处理：是
- 输出策略：覆盖原文件
- 质量参数：90
```

## 能做什么

- 支持本地文件、网络 URL、剪贴板图片三种输入来源。
- 支持 `PNG`、`JPEG/JPG`、`WEBP`、`GIF`、`BMP`、`TIFF`、`ICO` 等常见输出格式。
- 会根据格式差异处理透明度、质量参数和批量目录结构。
- 默认策略是“保留原文件，新生成目标格式文件”。
- 不适合裁剪、缩放、加水印或做复杂图像编辑。

## 使用示例

### 示例 1：转换单张图片

```text
请使用 any-picture-format skill 将这张图片转成 JPEG。
输入：`/tmp/demo.png`
输出：`/tmp/demo.jpg`
```

### 示例 2：从 URL 转换为 PNG

```text
请使用 any-picture-format skill 转换这个网络图片。
输入：`https://example.com/demo.webp`
输出：PNG 文件
另外，还有下列参数约束：
- 输出策略：新建文件
```

### 示例 3：批量转换整个目录

```text
请使用 any-picture-format skill 批量转换图片目录。
输入：`./assets/raw-images`，目标格式 `webp`
输出：转换后的图片文件
另外，还有下列参数约束：
- 递归处理：是
- 质量参数：85
```

## 输出

- 单文件转换时，默认在原文件旁生成同名新文件，例如 `image.png -> image.jpg`。
- 批量转换时，默认保留原目录结构和原文件名，只改变扩展名。
- 默认不会覆盖原文件；只有显式要求 `overwrite` 时才会覆盖。
- 如果是剪贴板或 URL 输入，技能会先落地临时输入，再生成目标输出。

## 配置

- 配置文件：`any-picture-format/config.yaml`
- 默认输出格式：`PNG`
- 默认输出策略：`new`
- 默认质量参数：`85`
- 批量递归默认值：`false`
- 高价值配置项：
  - `defaults.output_format`
  - `defaults.output_strategy`
  - `defaults.quality`
  - `output_formats`

## 备选用法（脚本/硬编码）

如果你已经明确知道输入路径和目标格式，直接使用脚本会更快。

### 验证输入

```bash
python3 any-picture-format/scripts/convert.py validate --source /path/to/image.png
```

### 转换单张图片

```bash
python3 any-picture-format/scripts/convert.py convert \
  --source /path/to/image.png \
  --format JPEG \
  --output /path/to/image.jpg \
  --strategy new \
  --quality 90
```

### 批量转换目录

```bash
python3 any-picture-format/scripts/convert.py batch \
  --directory /path/to/images \
  --format WEBP \
  --recursive \
  --strategy new \
  --quality 85
```

## 常见问题

### Q：PNG 转 JPEG 后透明背景怎么办？

A：JPEG 不支持透明度，通常会自动合成为纯色背景；如果你需要保留透明度，优先输出为 `PNG` 或 `WEBP`。

### Q：会覆盖原文件吗？

A：默认不会。只有明确要求 `overwrite`，或脚本里传入 `--strategy overwrite` 时才会覆盖。

### Q：批量转换时某个文件失败怎么办？

A：默认配置 `continue_on_error: true`，会继续处理其它文件；你可以根据最终报告定位失败项。

### Q：这个 skill 能顺手做裁剪或缩放吗？

A：不能。它的职责是“格式转换”，不是通用图像编辑。
