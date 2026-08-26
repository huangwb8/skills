# 工具包与命令

## 脚本

```bash
python3 scripts/validate_links.py DOCUMENT.md [CONFIG.yaml]
```

脚本负责加载配置并调用公共检查工具。默认配置来自 Skill 目录的 `config.yaml`。

## 直接命令

Verifier 的命令、版本和结果边界集中记录在 [`verifiers.md`](verifiers.md)。直接调用时需要自行传入配置参数，例如 `--timeout 10`、重复的 `--blacklist DOMAIN` 或 `--whitelist DOMAIN`；需要审计时追加 `--events EVENTS.ndjson --run-id RUN_ID`。

## 配置

```yaml
validation:
  timeout: 10
domain_whitelist: []
domain_blacklist: []
```

黑名单用于跳过不应访问的域名；白名单非空时只检查其中的域名。默认会避开本地、回环和内部地址。
