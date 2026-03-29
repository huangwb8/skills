# 校验清单

## 结构校验

- `SKILL.md` 仍然存在
- frontmatter 合法
- 关键 Markdown 链接未失效，且没有跳出目标 skill 根目录
- `checked_files` 没有把目标 skill 根目录下的 `README.md`、`CHANGELOG.md` 当成默认压缩对象
- 中间文件都在 `.compact-bensz-skills/run-{timestamp}/`
- `latest-run.txt` 指向的是本次验证对应的 run

## 语义校验

- 触发条件没有变窄或变偏
- 不适用范围仍然存在
- 安全限制仍然清楚
- 输入/输出/默认目录仍然可回答

## 收益校验

- 总字数下降
- 最大文件的字数明显下降，或有合理解释
- `SKILL.md` 比修改前更短、更聚焦

## 风险提示

如果出现以下情况，应停止并回看快照：
- frontmatter 被改坏
- 关键命令消失
- 输出文件名或路径说明消失
- 只读/只写限制被删
- 关键链接改成了越界相对路径
