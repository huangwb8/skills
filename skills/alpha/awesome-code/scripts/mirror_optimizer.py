#!/usr/bin/env python3
"""
Mirror Optimizer - 镜像源优化脚本

自动检测项目使用的包管理器，生成适配的国内镜像源配置。
支持 Docker、Python、Node.js、Go、Java、Ruby、Rust 等多种技术栈。
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import json

from _config import get_nested, load_skill_config

# 默认镜像源配置（当 config.yaml 缺失/不可读时的回退）
DEFAULT_PROVIDERS = {
    "aliyun": {
        "name": "阿里云",
        "priority": 1,
        "docker": "https://registry.cn-hangzhou.aliyuncs.com",
        "python": "https://mirrors.aliyun.com/pypi/simple/",
        "nodejs": "https://registry.npmmirror.com",
        "golang": "https://mirrors.aliyun.com/goproxy/",
        "java_maven": "https://maven.aliyun.com/repository/public",
        "java_gradle": "https://maven.aliyun.com/repository/public",
        "ruby": "https://gems.ruby-china.com",
        "rust": "https://mirrors.aliyun.com/crates.io-index/",
    },
    "tencent": {
        "name": "腾讯云",
        "priority": 2,
        "docker": "https://mirror.ccs.tencentyun.com",
        "python": "https://mirrors.cloud.tencent.com/pypi/simple/",
        "nodejs": "https://mirrors.cloud.tencent.com/npm/",
        "golang": "https://mirrors.tencent.com/go/",
        "java_maven": "https://mirrors.cloud.tencent.com/nexus/repository/maven-public/",
        "java_gradle": "https://mirrors.cloud.tencent.com/nexus/repository/maven-public/",
    },
    "tsinghua": {
        "name": "清华大学",
        "priority": 3,
        "docker": None,
        "python": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "nodejs": None,
        "golang": None,
        "java_maven": None,
        "java_gradle": None,
        "rust": "https://mirrors.tuna.tsinghua.edu.cn/git/crates.io-index.git",
    },
    "ustc": {
        "name": "中国科技大学",
        "priority": 4,
        "docker": None,
        "python": "https://mirrors.ustc.edu.cn/pypi/web/simple",
        "nodejs": None,
        "golang": "https://go-mirror.ustc.edu.cn/",
        "java_maven": None,
        "java_gradle": None,
        "rust": "https://mirrors.ustc.edu.cn/crates.io-index",
    },
}


# 包管理器检测规则（当 config.yaml 缺失/不可读时的回退）
DEFAULT_PACKAGE_MANAGERS = {
    "docker": {
        "files": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"],
        "config_dir": "docker",
        "priority": 10,
    },
    "python": {
        "files": ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py", "setup.cfg", "poetry.lock"],
        "config_dir": "python",
        "priority": 9,
    },
    "nodejs": {
        "files": ["package.json", "yarn.lock", "pnpm-lock.yaml", "package-lock.json"],
        "config_dir": "nodejs",
        "priority": 8,
    },
    "golang": {
        "files": ["go.mod", "go.sum", "Gopkg.lock", "Gopkg.toml"],
        "config_dir": "golang",
        "priority": 7,
    },
    "java_maven": {
        "files": ["pom.xml"],
        "config_dir": "java/maven",
        "priority": 6,
    },
    "java_gradle": {
        "files": ["build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "gradle.properties"],
        "config_dir": "java/gradle",
        "priority": 6,
    },
    "ruby": {
        "files": ["Gemfile", "gems.rb"],
        "config_dir": "ruby",
        "priority": 5,
    },
    "rust": {
        "files": ["Cargo.toml", "Cargo.lock"],
        "config_dir": "rust",
        "priority": 3,
    },
}


class MirrorOptimizer:
    """镜像源优化器"""

    def __init__(
        self,
        project_root: Path,
        preferred_provider: Optional[str] = None,
        skill_root: Optional[Path] = None,
    ):
        """
        初始化镜像源优化器

        Args:
            project_root: 项目根目录
            preferred_provider: 首选镜像源提供商 (aliyun, tencent, tsinghua 等)
        """
        self.project_root = Path(project_root).resolve()
        self._validate_project_root()

        self.skill_root = skill_root or Path(__file__).resolve().parent.parent
        config = load_skill_config(self.skill_root)
        mirror_config = get_nested(config, "mirror_optimization", default={})
        mirror_config = mirror_config if isinstance(mirror_config, dict) else {}

        self.providers = mirror_config.get("providers")
        if not isinstance(self.providers, dict) or not self.providers:
            self.providers = DEFAULT_PROVIDERS

        self.package_managers = mirror_config.get("package_managers")
        if not isinstance(self.package_managers, dict) or not self.package_managers:
            self.package_managers = DEFAULT_PACKAGE_MANAGERS

        default_provider = mirror_config.get("default_provider")
        provider = preferred_provider or default_provider or "aliyun"
        self.preferred_provider = str(provider).strip().lower()
        self.output_dir_name = str(mirror_config.get("output_dir", ".bensz-api/skills/mirror-optimizer/output"))
        self._validate_output_dir()
        self.generate_report_enabled = bool(mirror_config.get("generate_report", True))

        self.detected_managers: List[Dict[str, str]] = []
        self.mirror_dir = self.project_root / self.output_dir_name
        self.used_providers: Dict[str, str] = {}
        self.skipped_managers: List[Dict[str, str]] = []
        self._provider_cache: Dict[str, Tuple[str, str]] = {}

    def _validate_project_root(self) -> None:
        if not self.project_root.exists() or not self.project_root.is_dir():
            raise ValueError(f"项目根目录不存在或不是目录: {self.project_root}")

    def _validate_output_dir(self) -> None:
        output_dir = Path(self.output_dir_name)
        if output_dir.is_absolute() or any(part in {"..", ""} for part in output_dir.parts):
            raise ValueError(f"镜像源输出目录必须是相对路径: {self.output_dir_name}")

    def _validate_config_dir(self, config_dir: object, manager_type: str) -> str:
        if config_dir is None:
            raise ValueError(f"{manager_type} 缺少 config_dir 配置")
        path = Path(str(config_dir))
        if path.is_absolute() or any(part in {"..", ""} for part in path.parts):
            raise ValueError(f"{manager_type} config_dir 必须是相对路径: {config_dir}")
        return str(path)

    def _select_provider(self, manager_type: str) -> Tuple[str, str]:
        preferred = self.preferred_provider
        preferred_cfg = self.providers.get(preferred, {})
        preferred_url = preferred_cfg.get(manager_type) if isinstance(preferred_cfg, dict) else None
        if preferred_url:
            return preferred, preferred_url

        candidates: List[Tuple[int, str, str]] = []
        for name, cfg in self.providers.items():
            if not isinstance(cfg, dict):
                continue
            mirror_url = cfg.get(manager_type)
            if not mirror_url:
                continue
            priority = cfg.get("priority", 999)
            candidates.append((int(priority) if str(priority).isdigit() else 999, name, mirror_url))

        if candidates:
            candidates.sort(key=lambda x: (x[0], x[1]))
            return candidates[0][1], candidates[0][2]

        raise ValueError(f"未找到可用的镜像源提供商: {manager_type}")

    def _get_provider(self, manager_type: str) -> Tuple[str, str]:
        if manager_type in self._provider_cache:
            return self._provider_cache[manager_type]
        provider_name, mirror_url = self._select_provider(manager_type)
        self._provider_cache[manager_type] = (provider_name, mirror_url)
        self.used_providers[manager_type] = provider_name
        return provider_name, mirror_url

    @staticmethod
    def _extract_host(url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc or ""

    def detect_package_managers(self) -> List[Dict]:
        """
        检测项目中使用的包管理器

        Returns:
            检测到的包管理器列表（按优先级排序）
        """
        detected = []

        for manager_type, config in self.package_managers.items():
            if not isinstance(config, dict):
                self.skipped_managers.append({"type": manager_type, "reason": "配置格式错误（非字典）"})
                continue
            files = config.get("files")
            if not isinstance(files, list) or not files:
                self.skipped_managers.append({"type": manager_type, "reason": "缺少 files 列表"})
                continue
            try:
                config_dir = self._validate_config_dir(config.get("config_dir"), manager_type)
            except ValueError as exc:
                self.skipped_managers.append({"type": manager_type, "reason": str(exc)})
                continue
            priority_raw = config.get("priority", 0)
            try:
                priority = int(priority_raw)
            except Exception:
                priority = 0

            for file_pattern in files:
                file_path = self.project_root / file_pattern
                if file_path.exists():
                    detected.append({
                        "type": manager_type,
                        "config_dir": config_dir,
                        "priority": priority,
                        "detected_by": file_pattern,
                    })
                    break

        # 按优先级排序
        detected.sort(key=lambda x: x["priority"], reverse=True)
        self.detected_managers = detected

        return detected

    def generate_dockerfile_mirror(self, dockerfile_path: Path) -> Optional[str]:
        """
        生成优化的 Dockerfile（包含镜像源配置）

        Args:
            dockerfile_path: 原始 Dockerfile 路径

        Returns:
            优化后的 Dockerfile 内容
        """
        if not dockerfile_path.exists():
            return None

        original_content = dockerfile_path.read_text(encoding="utf-8")
        lines = original_content.split("\n")
        mirror_content = []
        inserted_mirror = False

        for i, line in enumerate(lines):
            mirror_content.append(line)

            # 在 FROM 指令后插入镜像源配置
            if line.strip().startswith("FROM") and not inserted_mirror:
                base_image = line.split()[1] if len(line.split()) > 1 else ""

                # 根据基础镜像类型选择镜像源
                mirror_config = self._get_docker_mirror_config(base_image)
                if mirror_config:
                    mirror_content.append("")
                    mirror_content.append("# 国内镜像源配置（使用构建参数控制是否启用）")
                    mirror_content.append("ARG USE_CHINA_MIRROR=false")
                    mirror_content.append("")
                    mirror_content.extend(mirror_config.split("\n"))
                    mirror_content.append("")
                    inserted_mirror = True

        return "\n".join(mirror_content)

    def _get_docker_mirror_config(self, base_image: str) -> str:
        """
        根据基础镜像获取镜像源配置

        Args:
            base_image: 基础镜像名称

        Returns:
            镜像源配置内容
        """
        provider_name, mirror_source = self._get_provider("docker")

        if "alpine" in base_image.lower():
            return f"""# Alpine 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \\
        sed -i 's/dl-cdn.alpinelinux.org/{mirror_source.split("//")[1]}/g' /etc/apk/repositories && \\
        echo "已切换到 {provider_name} Alpine 镜像源"; \\
    fi"""

        elif "ubuntu" in base_image.lower() or "debian" in base_image.lower():
            return f"""# Ubuntu/Debian 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \\
        sed -i 's@http://archive.ubuntu.com/@{mirror_source}/@g' /etc/apt/sources.list && \\
        sed -i 's@http://security.ubuntu.com/@{mirror_source}/@g' /etc/apt/sources.list && \\
        echo "已切换到 {provider_name} APT 镜像源"; \\
    fi"""

        elif "centos" in base_image.lower():
            return f"""# CentOS 镜像源
RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \\
        sed -i 's/mirrorlist=/#mirrorlist=/g' /etc/yum.repos.d/CentOS-*.repo && \\
        sed -i 's|#baseurl=http://mirror.centos.org|baseurl={mirror_source}|g' /etc/yum.repos.d/CentOS-*.repo && \\
        echo "已切换到 {provider_name} YUM 镜像源"; \\
    fi"""

        return "# 未识别的基础镜像类型，请手动配置镜像源"

    def generate_pip_config(self) -> str:
        """生成 pip 配置文件"""
        _, mirror_url = self._get_provider("python")
        trusted_host = self._extract_host(mirror_url)
        trusted_lines = f"trusted-host = {trusted_host}\n" if trusted_host else ""
        return f"""[global]
index-url = {mirror_url}
{trusted_lines}
[install]
{trusted_lines}"""

    def generate_npm_config(self) -> str:
        """生成 npm 配置文件"""
        _, mirror_url = self._get_provider("nodejs")
        return f"""registry={mirror_url}
"""

    def generate_yarn_config(self) -> str:
        """生成 yarn 配置文件"""
        _, mirror_url = self._get_provider("nodejs")
        return f"""npmRegistryServer: "{mirror_url}"
"""

    def generate_go_env(self) -> str:
        """生成 Go Modules 环境配置"""
        _, mirror_url = self._get_provider("golang")
        return f"""GOPROXY={mirror_url},direct
GOSUMDB=off
"""

    def generate_maven_settings(self) -> str:
        """生成 Maven settings.xml"""
        _, mirror_url = self._get_provider("java_maven")
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0
          http://maven.apache.org/xsd/settings-1.0.0.xsd">
  <mirrors>
    <mirror>
      <id>aliyun-maven</id>
      <name>Aliyun Maven Mirror</name>
      <url>{mirror_url}</url>
      <mirrorOf>central</mirrorOf>
    </mirror>
  </mirrors>
</settings>
"""

    def generate_gradle_init(self) -> str:
        """生成 Gradle init.gradle"""
        _, mirror_url = self._get_provider("java_gradle")
        return f"""allprojects {{
    repositories {{
        maven {{ url '{mirror_url}' }}
        mavenCentral()
    }}
}}
"""

    def generate_bundle_config(self) -> str:
        """生成 Bundler 配置"""
        _, mirror_url = self._get_provider("ruby")
        return f"""---
BUNDLE_MIRROR_URL: "{mirror_url}"
"""

    def generate_cargo_config(self) -> str:
        """生成 Cargo 配置"""
        provider_name, mirror_url = self._get_provider("rust")
        return f"""[source.crates-io]
replace-with = '{provider_name}'

[source.{provider_name}]
registry = "{mirror_url}"
"""

    def generate_configs(self) -> Dict[str, str]:
        """
        为检测到的所有包管理器生成配置文件

        Returns:
            配置文件路径到内容的映射
        """
        configs = {}

        for manager in self.detected_managers:
            manager_type = manager["type"]
            config_dir = manager["config_dir"]

            try:
                if manager_type == "docker":
                    dockerfile_path = self.project_root / "Dockerfile"
                    mirror_dockerfile = self.generate_dockerfile_mirror(dockerfile_path)
                    if mirror_dockerfile:
                        configs[f"{self.output_dir_name}/{config_dir}/Dockerfile.mirror"] = mirror_dockerfile

                elif manager_type == "python":
                    configs[f"{self.output_dir_name}/{config_dir}/pip.conf"] = self.generate_pip_config()

                elif manager_type == "nodejs":
                    # 检测是否使用 yarn
                    if (self.project_root / "yarn.lock").exists():
                        configs[f"{self.output_dir_name}/{config_dir}/.yarnrc.yml"] = self.generate_yarn_config()
                    else:
                        configs[f"{self.output_dir_name}/{config_dir}/.npmrc"] = self.generate_npm_config()

                elif manager_type == "golang":
                    configs[f"{self.output_dir_name}/{config_dir}/go.env"] = self.generate_go_env()

                elif manager_type == "java_maven":
                    configs[f"{self.output_dir_name}/{config_dir}/settings.xml"] = self.generate_maven_settings()

                elif manager_type == "java_gradle":
                    configs[f"{self.output_dir_name}/{config_dir}/init.gradle"] = self.generate_gradle_init()

                elif manager_type == "ruby":
                    configs[f"{self.output_dir_name}/{config_dir}/config"] = self.generate_bundle_config()

                elif manager_type == "rust":
                    configs[f"{self.output_dir_name}/{config_dir}/config.toml"] = self.generate_cargo_config()
            except ValueError as exc:
                self.skipped_managers.append({"type": manager_type, "reason": str(exc)})

        return configs

    def write_configs(self, configs: Dict[str, str]) -> List[Path]:
        """
        将配置写入文件

        Args:
            configs: 配置文件路径到内容的映射

        Returns:
            写入的文件路径列表
        """
        written_files = []

        # 创建配置输出目录
        self.mirror_dir.mkdir(parents=True, exist_ok=True)

        for file_path, content in configs.items():
            full_path = self.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            written_files.append(full_path)

        return written_files

    def generate_report(self) -> str:
        """
        生成镜像源优化报告

        Returns:
            Markdown 格式的报告内容
        """
        report = ["# 镜像源优化报告", "", f"**项目路径**: `{self.project_root}`", "",
                  "## 检测结果", "", f"检测到 **{len(self.detected_managers)}** 个包管理器：", ""]

        for manager in self.detected_managers:
            manager_type = manager["type"]
            provider = self.used_providers.get(manager_type, "未选择")
            report.append(
                f"- **{manager_type.upper()}**: 通过 `{manager['detected_by']}` 检测（provider: {provider})"
            )

        report.extend(["", "## 配置文件", "", "已生成的配置文件：", ""])

        # 列出所有生成的配置文件
        if self.mirror_dir.exists():
            for config_file in sorted(self.mirror_dir.rglob("*")):
                if config_file.is_file():
                    rel_path = config_file.relative_to(self.project_root)
                    report.append(f"- `{rel_path}`")
        if self.skipped_managers:
            report.extend(["", "## 跳过的包管理器", ""])
            for item in self.skipped_managers:
                report.append(f"- **{item['type'].upper()}**: {item['reason']}")

        detected_types = {m["type"] for m in self.detected_managers}
        use_yarn = (self.project_root / "yarn.lock").exists()

        report.extend(["", "## 使用方法", ""])
        if "docker" in detected_types:
            report.extend(["### Docker 镜像源", "",
                          "构建时启用国内镜像源：", "",
                          "```bash",
                          "docker build --build-arg USE_CHINA_MIRROR=true -t your-image .",
                          "```", ""])

        if "python" in detected_types:
            report.extend(["### Python pip", "",
                          "复制配置文件到用户目录：", "",
                          "```bash",
                          "mkdir -p ~/.pip",
                          f"cp {self.output_dir_name}/python/pip.conf ~/.pip/",
                          "```", ""])

        if "nodejs" in detected_types:
            if use_yarn:
                report.extend(["### Node.js yarn", "",
                              "复制配置文件到项目目录：", "",
                              "```bash",
                              f"cp {self.output_dir_name}/nodejs/.yarnrc.yml ./",
                              "```", ""])
            else:
                report.extend(["### Node.js npm", "",
                              "复制配置文件到项目目录：", "",
                              "```bash",
                              f"cp {self.output_dir_name}/nodejs/.npmrc ./",
                              "```", ""])

        if "golang" in detected_types:
            try:
                go_proxy = self._get_provider("golang")[1]
            except Exception:
                go_proxy = "https://mirrors.aliyun.com/goproxy/"
            report.extend(["### Go Modules", "",
                          "设置环境变量：", "",
                          "```bash",
                          f"export GOPROXY={go_proxy},direct",
                          "```",
                          "或使用配置文件：", "",
                          "```bash",
                          f"cp {self.output_dir_name}/golang/go.env ~/.config/go/env",
                          "```", ""])

        if "java_maven" in detected_types:
            report.extend(["### Java Maven", "",
                          "复制配置文件到 Maven 目录：", "",
                          "```bash",
                          "mkdir -p ~/.m2",
                          f"cp {self.output_dir_name}/java/maven/settings.xml ~/.m2/",
                          "```", ""])

        if "java_gradle" in detected_types:
            report.extend(["### Java Gradle", "",
                          "复制配置文件到 Gradle 目录：", "",
                          "```bash",
                          "mkdir -p ~/.gradle",
                          f"cp {self.output_dir_name}/java/gradle/init.gradle ~/.gradle/init.gradle",
                          "```", ""])

        if "ruby" in detected_types:
            report.extend(["### Ruby Bundler", "",
                          "复制配置文件到 Bundler 目录：", "",
                          "```bash",
                          "mkdir -p ~/.bundle",
                          f"cp {self.output_dir_name}/ruby/config ~/.bundle/config",
                          "```", ""])

        if "rust" in detected_types:
            report.extend(["### Rust Cargo", "",
                          "复制配置文件到 Cargo 目录：", "",
                          "```bash",
                          "mkdir -p ~/.cargo",
                          f"cp {self.output_dir_name}/rust/config.toml ~/.cargo/config.toml",
                          "```", ""])

        report.extend(["", "## 验证镜像源", "", "验证配置是否生效：", ""])
        if "python" in detected_types:
            report.extend(["```bash", "pip config list", "```"])
        if "nodejs" in detected_types:
            if use_yarn:
                report.extend(["```bash", "yarn config get npmRegistryServer", "```"])
            else:
                report.extend(["```bash", "npm config get registry", "```"])
        if "golang" in detected_types:
            report.extend(["```bash", "go env GOPROXY", "```"])
        if "java_maven" in detected_types:
            report.extend(["```bash", "mvn help:evaluate -Dexpression=settings.repositories -q -DforceStdout", "```"])
        if "java_gradle" in detected_types:
            report.extend(["```bash", f"cat {self.output_dir_name}/java/gradle/init.gradle", "```"])
        if "ruby" in detected_types:
            report.extend(["```bash", f"cat {self.output_dir_name}/ruby/config", "```"])
        if "rust" in detected_types:
            report.extend(["```bash", f"cat {self.output_dir_name}/rust/config.toml", "```"])

        report.extend(["", "## 切换回官方源", "",
                      "如需切换回官方源，删除相应配置文件即可：", "",
                      "```bash"])
        if "python" in detected_types:
            report.extend(["# Python", "rm ~/.pip/pip.conf", ""])
        if "nodejs" in detected_types:
            if use_yarn:
                report.extend(["# Node.js (yarn)", "rm .yarnrc.yml", ""])
            else:
                report.extend(["# Node.js (npm)", "rm .npmrc", ""])
        if "golang" in detected_types:
            report.extend(["# Go", "unset GOPROXY", ""])
        if "docker" in detected_types:
            report.extend(["# Docker", "# 重新构建时不传 USE_CHINA_MIRROR 参数", ""])
        report.extend(["```", "", "---", "",
                      f"*由 awesome-code/mirror-optimizer 生成 | 首选镜像源提供商: {self.preferred_provider}*"])

        return "\n".join(report)

    def optimize(self) -> Dict:
        """
        执行完整的镜像源优化流程

        Returns:
            优化结果字典
        """
        # 检测包管理器
        detected = self.detect_package_managers()

        if not detected:
            return {
                "success": False,
                "message": "未检测到任何需要配置镜像源的包管理器",
                "detected_managers": [],
                "skipped_managers": self.skipped_managers,
            }

        # 生成配置文件
        configs = self.generate_configs()
        if not configs:
            return {
                "success": False,
                "message": "检测到包管理器，但未生成任何镜像源配置",
                "detected_managers": detected,
                "skipped_managers": self.skipped_managers,
            }

        # 写入配置文件
        written_files = self.write_configs(configs)

        # 生成报告
        report_path = None
        if self.generate_report_enabled:
            report_content = self.generate_report()
            report_path = self.mirror_dir / "MIRROR_OPTIMIZATION_REPORT.md"
            report_path.write_text(report_content, encoding="utf-8")

        return {
            "success": True,
            "message": f"成功为 {len(detected)} 个包管理器配置镜像源",
            "detected_managers": detected,
            "config_files": [str(f.relative_to(self.project_root)) for f in written_files],
            "report_path": str(report_path.relative_to(self.project_root)) if report_path else None,
            "mirror_dir": str(self.mirror_dir.relative_to(self.project_root)),
            "skipped_managers": self.skipped_managers,
        }


def main():
    """命令行入口"""
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else Path.cwd()

    try:
        optimizer = MirrorOptimizer(project_path)
        result = optimizer.optimize()
    except Exception as exc:
        result = {
            "success": False,
            "message": f"镜像源优化失败: {exc}",
        }

    # 输出 JSON 格式结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
