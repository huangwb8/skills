# Dockerfile 镜像源优化模板

## Alpine 基础镜像

### 标准模板

```dockerfile
FROM alpine:3.18

# 接收构建参数，用于判断是否使用国内镜像源
ARG USE_CHINA_MIRROR=false

# 根据区域设置 Alpine 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && \
        echo "已切换到阿里云 Alpine 镜像源"; \
    fi

# 安装依赖
RUN apk add --no-cache \
    python3 \
    py3-pip \
    && rm -rf /var/cache/apk/*

# 配置 pip 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
        echo "已切换到阿里云 PyPI 镜像源"; \
    fi

# 应用代码
COPY . /app
WORKDIR /app

CMD ["python3", "app.py"]
```

### 多阶段构建

```dockerfile
# 构建阶段
FROM node:16-alpine AS builder

ARG USE_CHINA_MIRROR=false

RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories; \
    fi

RUN apk add --no-cache python3 make g++

COPY package*.json ./

RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        npm config set registry https://registry.npmmirror.com; \
    fi

RUN npm ci && npm run build

# 运行阶段
FROM node:16-alpine

ARG USE_CHINA_MIRROR=false

RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories; \
    fi

RUN apk add --no-cache tini

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./

ENTRYPOINT ["/sbin/tini", "--", "node", "dist/index.js"]
```

## Ubuntu/Debian 基础镜像

### 标准模板

```dockerfile
FROM ubuntu:22.04

# 避免交互式提示
ENV DEBIAN_FRONTEND=noninteractive

ARG USE_CHINA_MIRROR=false

# 备份原始源并切换到阿里云
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        cp /etc/apt/sources.list /etc/apt/sources.list.bak && \
        sed -i 's@http://archive.ubuntu.com/@https://mirrors.aliyun.com/@g' /etc/apt/sources.list && \
        sed -i 's@http://security.ubuntu.com/@https://mirrors.aliyun.com/@g' /etc/apt/sources.list && \
        echo "已切换到阿里云 APT 镜像源"; \
    fi

RUN apt-get update && \
    apt-get install -y \
        python3 \
        python3-pip \
        && rm -rf /var/lib/apt/lists/*

# 配置 pip 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/; \
    fi

WORKDIR /app
COPY . .

CMD ["python3", "app.py"]
```

## CentOS 基础镜像

```dockerfile
FROM centos:7

ARG USE_CHINA_MIRROR=false

# 切换到阿里云镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        sed -i 's/mirrorlist=/#mirrorlist=/g' /etc/yum.repos.d/CentOS-*.repo && \
        sed -i 's|#baseurl=http://mirror.centos.org|baseurl=https://mirrors.aliyun.com|g' /etc/yum.repos.d/CentOS-*.repo && \
        echo "已切换到阿里云 YUM 镜像源"; \
    fi

RUN yum install -y \
        python3 \
        python3-pip \
        && yum clean all

# 配置 pip 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/; \
    fi

WORKDIR /app
COPY . .

CMD ["python3", "app.py"]
```

## Node.js 应用

```dockerfile
FROM node:18-slim

ARG USE_CHINA_MIRROR=false

# 切换到阿里云镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        cp /etc/apt/sources.list /etc/apt/sources.list.bak && \
        sed -i 's@http://deb.debian.org/@https://mirrors.aliyun.com/@g' /etc/apt/sources.list && \
        apt-get update; \
    fi

# 安装依赖
RUN apt-get update && \
    apt-get install -y \
        python3 \
        build-essential \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package*.json ./

# 配置 npm 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        npm config set registry https://registry.npmmirror.com; \
    fi

RUN npm ci --only=production

COPY . .

CMD ["node", "index.js"]
```

## Python 应用

```dockerfile
FROM python:3.11-slim

ARG USE_CHINA_MIRROR=false

# 切换到阿里云镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        cp /etc/apt/sources.list /etc/apt/sources.list.bak && \
        sed -i 's@http://deb.debian.org/@https://mirrors.aliyun.com/@g' /etc/apt/sources.list && \
        apt-get update; \
    fi

RUN apt-get update && \
    apt-get install -y \
        gcc \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 配置 pip 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/; \
    fi

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

## Go 应用

```dockerfile
FROM golang:1.21-alpine AS builder

ARG USE_CHINA_MIRROR=false

# 切换 Alpine 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories; \
    fi

# 配置 Go 镜像源
ENV GOPROXY=https://mirrors.aliyun.com/goproxy/,direct
ENV GOSUMDB=off

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o main .

# 运行阶段
FROM alpine:3.18

ARG USE_CHINA_MIRROR=false

RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories; \
    fi

RUN apk add --no-cache ca-certificates

WORKDIR /root/

COPY --from=builder /app/main .

CMD ["./main"]
```

## Java 应用 (Maven)

```dockerfile
FROM maven:3.9-eclipse-temurin-17 AS builder

ARG USE_CHINA_MIRROR=false

# 切换 APT 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        cp /etc/apt/sources.list /etc/apt/sources.list.bak && \
        sed -i 's@http://deb.debian.org/@https://mirrors.aliyun.com/@g' /etc/apt/sources.list && \
        apt-get update; \
    fi

# 配置 Maven 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        mkdir -p /root/.m2 && \
        echo '<settings><mirrors><mirror><id>aliyun-maven</id><name>Aliyun Maven</name><url>https://maven.aliyun.com/repository/public</url><mirrorOf>central</mirrorOf></mirror></settings>' > /root/.m2/settings.xml; \
    fi

WORKDIR /app

COPY pom.xml .
RUN mvn dependency:go-offline

COPY src ./src
RUN mvn clean package -DskipTests

# 运行阶段
FROM eclipse-temurin:17-jre

ARG USE_CHINA_MIRROR=false

RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        cp /etc/apt/sources.list /etc/apt/sources.list.bak && \
        sed -i 's@http://deb.debian.org/@https://mirrors.aliyun.com/@g' /etc/apt/sources.list && \
        apt-get update; \
    fi

WORKDIR /app

COPY --from=builder /app/target/*.jar app.jar

ENTRYPOINT ["java", "-jar", "app.jar"]
```

## Java 应用 (Gradle)

```dockerfile
FROM gradle:8-jdk17 AS builder

ARG USE_CHINA_MIRROR=false

# 配置 Gradle 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        mkdir -p /root/.gradle && \
        echo 'allprojects { repositories { maven { url "https://maven.aliyun.com/repository/public" } mavenCentral() } }' > /root/.gradle/init.gradle; \
    fi

WORKDIR /app

COPY build.gradle settings.gradle ./
RUN gradle dependencies --refresh-dependencies

COPY src ./src
RUN gradle clean build -x test

# 运行阶段
FROM eclipse-temurin:17-jre

WORKDIR /app

COPY --from=builder /app/build/libs/*.jar app.jar

ENTRYPOINT ["java", "-jar", "app.jar"]
```

## Ruby 应用

```dockerfile
FROM ruby:3.2-slim

ARG USE_CHINA_MIRROR=false

# 切换 APT 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        cp /etc/apt/sources.list /etc/apt/sources.list.bak && \
        sed -i 's@http://deb.debian.org/@https://mirrors.aliyun.com/@g' /etc/apt/sources.list && \
        apt-get update; \
    fi

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        nodejs \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 配置 Bundler 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        bundle config mirror.https://rubygems.org https://gems.ruby-china.com; \
    fi

COPY Gemfile Gemfile.lock ./
RUN bundle install

COPY . .

CMD ["rails", "server", "-b", "0.0.0.0"]
```

## 通用技巧

### 条件配置函数

```dockerfile
# 定义函数简化配置
RUN setup_mirrors() { \
        if [ "$USE_CHINA_MIRROR" = "true" ]; then \
            # Alpine
            if [ -f /etc/apk/repositories ]; then \
                sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories; \
            # Debian/Ubuntu
            elif [ -f /etc/apt/sources.list ]; then \
                sed -i 's@http://deb.debian.org/@https://mirrors.aliyun.com/@g' /etc/apt/sources.list; \
            fi; \
        fi; \
    } && setup_mirrors
```

### 多镜像源配置

```dockerfile
ARG USE_CHINA_MIRROR=false

# 主镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories; \
        echo "https://mirrors.tuna.tsinghua.edu.cn/alpine/v3.18/community" >> /etc/apk/repositories; \
    fi
```

### 构建参数传递

```bash
# 构建时启用国内镜像源
docker build --build-arg USE_CHINA_MIRROR=true -t myapp .

# 使用官方源
docker build -t myapp .
```

### Docker Compose 集成

```yaml
version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        USE_CHINA_MIRROR: ${USE_CHINA_MIRROR:-false}
    image: myapp:latest
```

```bash
# 使用国内镜像源构建
USE_CHINA_MIRROR=true docker-compose build
```
