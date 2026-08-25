## 更新

```
version = 4.3.8
请你：
- 根据源代码的实际变化写 ./CHANGELOG.md 、 优化 README 或 优化 @install 里的脚本。
- 创建新的tag v{version}。 用 git-commit skill 提交commit，commit信息里要带版本号。
- 用 git-publish-release skill 发布新的release。
```

# 日常

---

目前，本项目有非常巨大的变动。 直接改造成 /Volumes/2T01/Test/@legacy-projects/old-skills （只读）的形式； 基本上大部分东西都直接挪过来。 这是一些冲突处理的方式：

- 本项目的 @install 脚本的能力应该直接融入 install-bensz-skills 这个skill里

- 本项目里目前已经存在的skills，都是比较成熟的，适合发布的skill。 它们的位置可以放在 ./skills/alpha 里。 有一些skill，仅在 /Volumes/2T01/Test/@legacy-projects/old-skills 里出现但本项目目前还没有的，都是一些还没有开发成熟的skill； 应该放在 ./skills/beta 里。
- install-bensz-skills 的逻辑要优化：默认仅安装  ./skills/alpha 里的skill。除非用户特别指定，否则约不能安装  ./skills/alpha 里的skill。 install-bensz-skills 的远程安装的脚本应该要调整下，确保仅安装  ./skills/alpha 里的skill
- 系统文件冲突： Prompts.md、CHANGELOG.md、LICENSE、AGENTS.md、CLAUDE.md、readme类md、skills.code-workspace 以本项目为准。
- 因为有很多新目录，所以目录管理是有所讲究的； 以 /Volumes/2T01/Test/@legacy-projects/old-skills 里 AGENTS.md 的约定为准

请进行改动。 本项目已经事先进行git备份，因此你可以大胆操作。

---

最近，./install-bensz-skills 的策略有一些轻的变化。  请问， @install 里的脚本要不要对齐一下？ 如果有必要，请你优化一下。

---

我倾向于拒绝这个pr。 请你指出 docs/pr-reviews/Git-PR-Review_huangwb8_skills_pr-1_20260330184127.md 里揭示的诸多问题，并且善意地表示目前暂时不接受改变这种改变prompt类的提交；因为目前skill正处于我个人的频繁开发中。 你帮我回复该pr的作者，然后关闭这个pr。

---

本项目有一个pr: https://github.com/huangwb8/skills/pull/1 。 请对它进行评估。 结果保存在： docs/pr-reviews 。 我怀疑：

- 作者有可能通过提交不太重要的pr，从而来蹭贡献者。因为我看了作者的仓库，他fork了很多ai相关的仓库。 所以，他有可能在系统地通过这些工作进行虚假地进行贡献，来给自己刷简历。如果是这种情况，我不打算merge他的pr
- 其它你觉得可疑的地方也要说。
