# Prompt Guidelines

1. **理解需求与模式**：
   - 把用户的 `user_need` 拆成三部分：意图（是什么）、视觉元素（有哪些节点/文本/布局）、硬约束（颜色/比例/输出格式）。
   - 先确定 `mode`：默认 `general`；技术路线图/flowchart 用 `roadmap`；原理图/机制图/架构图用 `schematic`。
   - 在 prompt 中用明确的 bullet（如 `- elements`、`- layout`）列出每个部分，避免模糊说法。

2. **Prompt 模板结构**：
   ```
   你是一个精通 Nano Banana / Gemini 的绘图模型，负责把输入的需求转化为可执行 prompt。
   场景：{用途 / 受众}
   元素：
   - {元素 1}
   - {元素 2}
   风格：{色调 / 质感 / 字体 / 参考图}
   排除项：{千万别做的事情}
   输出产物：PNG，要求 {尺寸 / 4K / 透明背景 / 其他}
   ```
   把 `visual_constraints` 填入 `风格` 与 `输出` 中，把 `reference_images` 作为“样式参考图”说明。

3. **Mode Preset 要点**：
   - `general`：忠实复述用户需求，主体清晰，画面稳定，避免无关元素。
   - `roadmap`：白底、A4/打印可读、3-5 个阶段、阶段标题条、圆角节点、主链粗箭头、风险/备选细线或虚线；禁止图内总标题/caption。
   - `schematic`：白底、16:10 友好、分组大框、圆角节点、机制链/模块关系清楚、主链粗箭头、辅助/验证细箭头或虚线；严格保留用户术语。
   - `roadmap` 与 `schematic` 都必须强约束文字：水平、清晰、框内留白、短句换行、禁止乱码/扭曲/艺术字/手写/透视。

4. **多轮优化提示语**：
   - 第一轮不要带过多假设，直接复述需求。
   - 之后的轮次在 prompt 末尾附上 `feedback` 段，比如：
     ```
     Feedback:
     - 上轮评估：文字与背景对比不足
     - 修改方向：增强对比、加边框
     ```
   - 指定 `round` 和 `max_rounds` 以便 meta 记录。

5. **AI 视觉评估入参**：
   - `evaluation` 段至少要覆盖 `score`（0-10）、`passed`（true/false）、`must_fix`、`prompt_patch`。
   - 若本轮未通过，下一轮 prompt 必须把 `must_fix` / `prompt_patch` 显式合并进去。

6. **安全与隐私**：
   - 不要在 prompt 中暴露 API key、绝对路径等敏感信息。
   - 引用参考图时只描述风格，不附带具体文件路径（由 workflow 在 workspace 内提供）。

7. **记录**：
   - 把每轮 prompt 写入 `.draw-plot/run-<timestamp>/rounds/round-XX/prompt.txt`，便于复现与审计。
   - 若远端模型不支持文本规划，可回退为“用户需求 + 护栏模板 + 上轮修复项”的本地模板。
