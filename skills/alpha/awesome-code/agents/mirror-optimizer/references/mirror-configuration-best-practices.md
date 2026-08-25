# 镜像源配置最佳实践

## 核心原则

### 1. 透明性原则

镜像源配置应该是透明、可控的，而不是隐藏在复杂的脚本中。

```dockerfile
# ✅ 推荐：使用构建参数控制
ARG USE_CHINA_MIRROR=false
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories; \
    fi

# ❌ 避免：无条件切换镜像源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories
```

### 2. 可逆性原则

用户应该能够轻松切换回官方源。

```bash
# 提供一键切换脚本
./scripts/switch-mirror.sh --source aliyun
./scripts/switch-mirror.sh --source official
```

### 3. 适应性原则

根据部署环境自动选择合适的镜像源。

```yaml
# .github/workflows/deploy.yml
- name: Detect region and set mirror
  run: |
    if [[ "${{ secrets.DEPLOY_REGION }}" == "cn" ]]; then
      export USE_CHINA_MIRROR=true
    fi
```

### 4. 验证性原则

配置后必须验证镜像源的可用性。

```bash
# 验证 pip 镜像源
pip config list
pip install --dry-run some-package

# 验证 npm 镜像源
npm config get registry
npm ping
```

## 安全注意事项

### 1. 只使用可信镜像源

- 优先使用阿里云、腾讯云、华为云等知名云服务商
- 避免使用来源不明的镜像源
- 定期检查镜像源的 HTTPS 证书

### 2. 验证镜像完整性

```dockerfile
# Dockerfile: 添加镜像验证
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        apk add --no-cache curl && \
        curl -fSs https://mirrors.aliyun.com > /dev/null && \
        echo "镜像源可用"; \
    fi
```

### 3. 配置镜像源备份

```ini
# pip.conf
[global]
index-url = https://mirrors.aliyun.com/pypi/simple/
extra-index-url = https://pypi.org/simple/
```

## 常见问题

### Q1: 镜像源配置后仍然很慢？

**A**: 检查以下几点：
1. 确认配置文件位置正确（用户目录 vs 项目目录）
2. 验证镜像源 URL 是否可访问
3. 尝试切换到其他镜像源提供商
4. 检查网络代理设置

### Q2: 如何在生产环境使用镜像源？

**A**: 建议做法：
1. 在 CI/CD 流程中使用构建参数控制
2. 在生产环境配置内部镜像仓库
3. 定期同步官方源到内部仓库
4. 做好镜像源的监控和告警

### Q3: 镜像源更新不及时怎么办？

**A**: 解决方案：
1. 配置多个镜像源（主备）
2. 设置合理的超时时间
3. 使用 CDN 加速的镜像源
4. 必要时回退到官方源

## 技术栈特定指南

### Python/pip

```bash
# 全局配置
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://mirrors.aliyun.com/pypi/simple/
trusted-host = mirrors.aliyun.com
EOF

# 项目级配置
export PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
```

### Node.js/npm

```bash
# 全局配置
npm config set registry https://registry.npmmirror.com

# 项目级配置
echo "registry=https://registry.npmmirror.com" > .npmrc
```

### Go Modules

```bash
# 环境变量
export GOPROXY=https://mirrors.aliyun.com/goproxy/,direct
export GOSUMDB=off

# Go 1.13+ 自动使用环境变量
go mod download
```

### Docker

```dockerfile
# 多阶段构建时每个阶段都需要配置
FROM node:16-alpine AS builder
ARG USE_CHINA_MIRROR=false
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        npm config set registry https://registry.npmmirror.com; \
    fi

FROM node:16-alpine
ARG USE_CHINA_MIRROR=false
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        npm config set registry https://registry.npmmirror.com; \
    fi
```

## 自动化配置脚本

### 检测脚本

```bash
#!/bin/bash
# detect-mirrors.sh

# 检测项目类型并建议镜像源配置
if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
    echo "检测到 Python 项目，建议配置 pip 镜像源"
fi

if [ -f "package.json" ]; then
    echo "检测到 Node.js 项目，建议配置 npm/yarn 镜像源"
fi

if [ -f "go.mod" ]; then
    echo "检测到 Go 项目，建议配置 GOPROXY"
fi
```

### 一键配置脚本

```bash
#!/bin/bash
# setup-mirrors.sh

set -e

MIRROR_SOURCE=${1:-aliyun}

case "$MIRROR_SOURCE" in
    aliyun)
        PIP_MIRROR="https://mirrors.aliyun.com/pypi/simple/"
        NPM_MIRROR="https://registry.npmmirror.com"
        GO_MIRROR="https://mirrors.aliyun.com/goproxy/"
        ;;
    tencent)
        PIP_MIRROR="https://mirrors.cloud.tencent.com/pypi/simple/"
        NPM_MIRROR="https://mirrors.cloud.tencent.com/npm/"
        GO_MIRROR="https://mirrors.tencent.com/go/"
        ;;
    *)
        echo "不支持的镜像源: $MIRROR_SOURCE"
        exit 1
        ;;
esac

# Python
if [ -f "requirements.txt" ]; then
    mkdir -p ~/.pip
    cat > ~/.pip/pip.conf << EOF
[global]
index-url = $PIP_MIRROR
trusted-host = mirrors.aliyun.com
EOF
    echo "✓ 已配置 pip 镜像源"
fi

# Node.js
if [ -f "package.json" ]; then
    echo "registry=$NPM_MIRROR" > .npmrc
    echo "✓ 已配置 npm 镜像源"
fi

# Go
if [ -f "go.mod" ]; then
    cat > ~/.config/go/env << EOF
GOPROXY=$GO_MIRROR,direct
GOSUMDB=off
EOF
    echo "✓ 已配置 Go 镜像源"
fi
```
