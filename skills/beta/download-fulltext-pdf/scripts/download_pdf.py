#!/usr/bin/env python3
"""
核心下载逻辑（多源策略）
"""
import sys
import re
import json
import hashlib
import random
import requests
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# 尝试导入可选依赖
try:
    from scihub import SciHub
    HAS_SCIHUB = True
except ImportError:
    HAS_SCIHUB = False

# 自动安装缺失的可选依赖
def auto_install_dependencies():
    """自动安装缺失的可选依赖"""
    missing = []

    if not HAS_SCIHUB:
        missing.append("scihub")

    if not missing:
        return True

    # 提醒用户将要安装的包
    print(f"📦 检测到缺失依赖: {', '.join(missing)}", file=sys.stderr)
    print(f"💡 正在自动安装，请稍候...", file=sys.stderr)

    import subprocess

    for package in missing:
        try:
            print(f"   安装 {package}...", file=sys.stderr)
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                print(f"   ✅ {package} 安装成功", file=sys.stderr)
            else:
                print(f"   ❌ {package} 安装失败: {result.stderr}", file=sys.stderr)
                return False
        except subprocess.TimeoutExpired:
            print(f"   ❌ {package} 安装超时", file=sys.stderr)
            return False
        except Exception as e:
            print(f"   ❌ {package} 安装出错: {e}", file=sys.stderr)
            return False

    return True


class PDFDownloader:
    """多源 PDF 下载器"""

    def __init__(self, doi: str, output_path: Path, config: dict = None):
        self.doi = doi.strip()
        self.output_path = output_path
        self.config = config or {}
        self.sources_tried = []

        # 从配置中获取参数
        self.scihub_config = self.config.get("download", {}).get("scihub", {})
        self.arxiv_config = self.config.get("download", {}).get("arxiv", {})
        self.unpaywall_config = self.config.get("download", {}).get("unpaywall", {})

    def _safe_relpath_under_cwd(self, relpath: str) -> Path:
        """
        将相对路径安全地解析到 cwd 下。
        - 禁止绝对路径
        - 禁止包含 '..' 进行越界
        """
        if not relpath:
            raise ValueError("state_file 不能为空")

        p = Path(relpath)
        if p.is_absolute():
            raise ValueError(f"state_file 必须是相对路径: {relpath}")
        if any(part == ".." for part in p.parts):
            raise ValueError(f"state_file 不允许包含 '..': {relpath}")

        return (Path.cwd().resolve() / p).resolve()

    def _normalize_emails(self) -> List[str]:
        """从配置读取邮箱列表（兼容 emails / email 两种字段），并去重保序。"""
        emails: List[str] = []

        raw_emails = self.unpaywall_config.get("emails")
        if isinstance(raw_emails, list):
            emails.extend([str(x).strip() for x in raw_emails if str(x).strip()])

        legacy = str(self.unpaywall_config.get("email", "")).strip()
        if legacy and not emails:
            emails.append(legacy)

        # 去重（保序）
        seen = set()
        out: List[str] = []
        for e in emails:
            if e not in seen:
                seen.add(e)
                out.append(e)
        return out

    def _choose_unpaywall_email_order(self, emails: List[str]) -> List[str]:
        """
        选择本次请求优先使用的 email，并生成“重试顺序”（用于 429/5xx 等降级重试）。
        支持策略：
        - round_robin：持久化轮询（state_file 相对 cwd）
        - hash_doi：按 DOI 哈希分桶（无状态，默认更可复现）
        - random：随机
        """
        if not emails:
            return []
        if len(emails) == 1:
            return emails[:]

        strategy = str(self.unpaywall_config.get("email_strategy", "hash_doi")).strip() or "hash_doi"
        strategy = strategy.lower()

        start_idx = 0
        if strategy == "random":
            start_idx = random.randrange(len(emails))
        elif strategy == "round_robin":
            state_file = str(self.unpaywall_config.get("state_file", ".bensz-api/skills/download-fulltext-pdf/state/unpaywall_email_state.json"))
            try:
                state_path = self._safe_relpath_under_cwd(state_file)
                state_path.parent.mkdir(parents=True, exist_ok=True)
                state: Dict[str, Any] = {}
                if state_path.exists():
                    try:
                        state = json.loads(state_path.read_text(encoding="utf-8"))
                    except Exception:
                        state = {}
                start_idx = int(state.get("next_index", 0)) % len(emails)
                state["next_index"] = (start_idx + 1) % len(emails)
                state_path.write_text(json.dumps(state, ensure_ascii=True), encoding="utf-8")
            except Exception:
                # 轮询状态文件写入失败时，降级到 hash_doi（无状态）
                strategy = "hash_doi"

        if strategy == "hash_doi":
            h = hashlib.sha256(self.doi.encode("utf-8")).hexdigest()
            start_idx = int(h, 16) % len(emails)

        ordered = emails[start_idx:] + emails[:start_idx]
        return ordered

    def _pick_unpaywall_pdf_urls(self, data: Dict[str, Any]) -> List[str]:
        """从 Unpaywall 响应里提取候选 PDF URL（优先 url_for_pdf，其次 url）。"""
        urls: List[str] = []

        def add_location(loc: Any) -> None:
            if not isinstance(loc, dict):
                return
            pdf_url = loc.get("url_for_pdf")
            if isinstance(pdf_url, str) and pdf_url.strip():
                urls.append(pdf_url.strip())
                return
            url = loc.get("url")
            if isinstance(url, str) and url.strip():
                urls.append(url.strip())

        add_location(data.get("best_oa_location"))
        oa_locations = data.get("oa_locations")
        if isinstance(oa_locations, list):
            for loc in oa_locations:
                add_location(loc)

        # 去重保序
        seen = set()
        out: List[str] = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                out.append(u)
        return out

    def download_from_scihub(self) -> Tuple[bool, str]:
        """从 Sci-Hub 下载"""
        global HAS_SCIHUB

        # 首次使用时尝试自动安装
        if not HAS_SCIHUB:
            if auto_install_dependencies():
                # 尝试重新导入
                try:
                    from scihub import SciHub
                    HAS_SCIHUB = True
                except ImportError:
                    return False, "scihub 库安装失败"
            else:
                return False, "scihub 库自动安装失败，请手动运行: pip install scihub"

        if not self.scihub_config.get("enabled", True):
            return False, "Sci-Hub 已禁用"

        try:
            sh = SciHub()
            # 使用配置的域名（如果有）
            domain = self.scihub_config.get("domain")
            if domain:
                sh.base_domain = domain

            # 尝试下载
            result = sh.download(self.doi, path=str(self.output_path))
            if result and self.output_path.exists():
                return True, "Sci-Hub"
            return False, "下载失败"
        except Exception as e:
            error_msg = str(e).lower()
            if "captcha" in error_msg or "cloudflare" in error_msg:
                return False, "CAPTCHA 验证失败"
            if "not found" in error_msg or "404" in error_msg:
                return False, "未找到文献"
            return False, str(e)

    def download_from_arxiv(self) -> Tuple[bool, str]:
        """从 arXiv 下载"""
        if not self.arxiv_config.get("enabled", True):
            return False, "arXiv 已禁用"

        arxiv_id = self._extract_arxiv_id()
        if not arxiv_id:
            return False, "非 arXiv 论文"

        base_url = self.arxiv_config.get("base_url", "https://arxiv.org/pdf")
        url = f"{base_url}/{arxiv_id}.pdf"

        try:
            timeout = self.arxiv_config.get("timeout", 30)
            response = requests.get(url, timeout=timeout)

            if response.status_code == 200:
                # 验证内容是 PDF
                content = response.content
                if content.startswith(b"%PDF-"):
                    self.output_path.write_bytes(content)
                    return True, "arXiv"
                return False, "返回内容非 PDF 格式"
            elif response.status_code == 404:
                return False, "arXiv 中未找到"
            else:
                return False, f"HTTP {response.status_code}"
        except requests.Timeout:
            return False, "请求超时"
        except Exception as e:
            return False, str(e)

    def download_from_unpaywall(self) -> Tuple[bool, str]:
        """从 Unpaywall 下载（合法开放获取）"""
        if not self.unpaywall_config.get("enabled", True):
            return False, "Unpaywall 已禁用"

        api_url = self.unpaywall_config.get("api_url", "https://api.unpaywall.org/v2")
        emails = self._normalize_emails()
        email_order = self._choose_unpaywall_email_order(emails)

        url = f"{api_url}/{self.doi}"

        try:
            timeout = self.unpaywall_config.get("timeout", 30)
            last_status: Optional[int] = None
            last_err: Optional[str] = None

            # 无邮箱时也允许请求（但某些情况下会被拒绝/限流）
            attempts = email_order if email_order else [""]
            for email in attempts:
                params = {}
                if email:
                    params["email"] = email
                response = requests.get(url, params=params, timeout=timeout)
                last_status = response.status_code

                if response.status_code == 200:
                    data = response.json()
                    break

                # 这些状态码换邮箱/重试有可能改善；否则直接失败即可。
                last_err = f"Unpaywall API 返回 {response.status_code}"
                if response.status_code in (401, 403, 429) or 500 <= response.status_code <= 599:
                    continue
                return False, last_err
            else:
                return False, last_err or f"Unpaywall API 返回 {last_status}"

            # 检查是否有开放获取版本
            if not data.get("is_oa"):
                return False, "无开放获取版本"

            # 提取候选 URL（best_oa_location + oa_locations）
            candidate_urls = self._pick_unpaywall_pdf_urls(data)
            if not candidate_urls:
                return False, "无可用的 OA 链接（缺少 url_for_pdf/url）"

            # 下载 PDF（逐个尝试）
            last_pdf_status: Optional[int] = None
            for pdf_url in candidate_urls:
                pdf_response = requests.get(pdf_url, timeout=timeout, allow_redirects=True)
                last_pdf_status = pdf_response.status_code
                if pdf_response.status_code != 200:
                    continue
                content = pdf_response.content
                if content.startswith(b"%PDF-"):
                    self.output_path.write_bytes(content)
                    return True, "Unpaywall"
            return False, f"PDF 下载失败: HTTP {last_pdf_status}"

        except requests.Timeout:
            return False, "请求超时"
        except Exception as e:
            return False, str(e)

    def download_from_direct(self) -> Tuple[bool, str]:
        """尝试直接从期刊官网下载"""
        # 构建 DOI 解析 URL
        doi_url = f"https://doi.org/{self.doi}"

        try:
            # 获取重定向后的 URL（实际期刊页面）
            response = requests.get(doi_url, timeout=30, allow_redirects=True)
            final_url = response.url

            # 尝试常见的 PDF 路径模式
            pdf_patterns = [
                f"{final_url}/pdf",
                f"{final_url}.pdf",
                f"{final_url}/full.pdf",
                final_url.replace("/article/", "/article/pdf/"),
            ]

            for pdf_url in pdf_patterns:
                try:
                    pdf_response = requests.get(pdf_url, timeout=30)
                    if pdf_response.status_code == 200:
                        content = pdf_response.content
                        if content.startswith(b"%PDF-"):
                            self.output_path.write_bytes(content)
                            return True, "期刊官网"
                except Exception:
                    continue

            return False, "未找到直接 PDF 链接"

        except Exception as e:
            return False, str(e)

    def _extract_arxiv_id(self) -> Optional[str]:
        """从 DOI 中提取 arXiv ID"""
        # 常见的 arXiv DOI 格式
        # 10.48550/arXiv.2301.12345
        # doi.org/10.48550/arXiv.2301.12345

        arxiv_patterns = [
            r"arxiv\.(\d+\.\d+)",  # arXiv.ID
            r"arxiv/(\d+\.\d+)",  # arXiv/ID
        ]

        for pattern in arxiv_patterns:
            match = re.search(pattern, self.doi.lower())
            if match:
                return match.group(1)

        # 检查是否是 arXiv DOI 前缀
        if self.doi.startswith("10.48550/"):
            suffix = self.doi.split("/")[-1]
            if suffix.lower().startswith("arxiv."):
                parts = suffix.split(".")
                # arXiv ID 格式: YYMM.NNNNN 或 YYMMNNN
                if len(parts) >= 3:
                    return f"{parts[-2]}.{parts[-1]}"  # 返回字符串而非列表

        return None

    def download(self) -> Tuple[bool, str, str]:
        """执行多源下载策略"""
        # 策略 1: arXiv（如果检测到 arXiv ID）
        arxiv_id = self._extract_arxiv_id()
        if arxiv_id:
            self.sources_tried.append("arXiv")
            success, source = self.download_from_arxiv()
            if success:
                return True, source, "成功"

        # 策略 2: Sci-Hub
        self.sources_tried.append("Sci-Hub")
        success, source = self.download_from_scihub()
        if success:
            return True, source, "成功"

        # 策略 3: Unpaywall（合法 OA）
        self.sources_tried.append("Unpaywall")
        success, source = self.download_from_unpaywall()
        if success:
            return True, source, "成功"

        # 策略 4: 直接从期刊官网
        self.sources_tried.append("期刊官网")
        success, source = self.download_from_direct()
        if success:
            return True, source, "成功"

        # 所有源失败
        tried = ", ".join(self.sources_tried)
        return False, "", f"尝试过的源: {tried}"


def load_config(config_path: Path) -> dict:
    """加载配置文件"""
    import yaml

    if not config_path.exists():
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    if len(sys.argv) < 3:
        print("用法: python download_pdf.py <doi> <output_path> [config_path]", file=sys.stderr)
        sys.exit(1)

    doi = sys.argv[1]
    output_path = Path(sys.argv[2]).expanduser().resolve()

    # 加载配置（可选）
    config = {}
    if len(sys.argv) >= 4:
        config_path = Path(sys.argv[3])
        config = load_config(config_path)

    downloader = PDFDownloader(doi, output_path, config)
    success, source, message = downloader.download()

    if success:
        print(f"SUCCESS:{source}")
        print(f"FILE:{output_path}")
        print(f"SIZE:{output_path.stat().st_size}")
        print(f"SOURCES_TRIED:{','.join(downloader.sources_tried)}")
        return 0
    else:
        print(f"FAILURE:{message}", file=sys.stderr)
        print(f"SOURCES_TRIED:{','.join(downloader.sources_tried)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
