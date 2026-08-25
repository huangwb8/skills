# 保留清单

压缩前后，至少逐项确认以下信息没有丢失。

## SKILL.md frontmatter

- `name`
- `description`
- `metadata.author`
- `metadata.keywords`
- `metadata.keywords` 仍包含 skill 名

## 触发与边界

- 什么时候应该用这个 skill
- 什么时候不该用
- 用户最小输入是什么
- 最终输出是什么

## 行为约束

- 默认工作区 / 隐藏目录
- 测试区或测试约束
- 只读/只写边界
- 必须执行的步骤
- 失败时的处理方式

## 关键实现信息

- 唯一或主要命令示例
- 关键脚本路径
- 配置文件路径或关键配置键
- 会影响行为的文件命名规则
- 默认待压缩范围是否仍限定在工作型 Markdown，而非 `README.md` / `CHANGELOG.md`

## 跨 skill 约定

- 与 `bensz-collect-bugs` 的协作约定
- 与 `parallel-vibe`、`auto-test-skill` 等强依赖 skill 的衔接方式
