#!/usr/bin/env python3
"""
Markdown 引用验证脚本

功能：
1. 提取 Markdown 文档中的所有 URL 引用
2. 验证 URL 可达性
3. 返回验证结果供 AI 进一步处理
"""

import re
import sys
import json
import argparse
import hashlib
import shutil
from pathlib import Path
from urllib.parse import unquote, urlparse
from typing import List, Dict, Optional
import subprocess
import os


def _load_verifier_runtime():
    """Load the repository kernel without requiring an editable install."""
    kernel_src = Path(__file__).resolve().parents[4] / 'packages' / 'bensz-skill-kernel' / 'src'
    if str(kernel_src) not in sys.path:
        sys.path.insert(0, str(kernel_src))
    from bensz_skill_kernel import Evidence, VerificationRequest, VerifierRunner, build_builtin_registry
    return Evidence, VerificationRequest, VerifierRunner, build_builtin_registry


def get_skill_root() -> Path:
    """
    获取技能根目录的绝对路径。

    无论脚本从哪里调用，都能正确定位到技能根目录（包含 SKILL.md 的目录）。

    工作原理：
    1. 首先尝试从 __file__ 定位（脚本自身的绝对路径）
    2. 如果 __file__ 不可用（如某些执行环境），回退到环境变量
    3. 最后回退到当前工作目录下的 .claude/skills/{skill_name}

    Returns:
        技能根目录的绝对路径
    """
    # 方法1：通过 __file__ 定位（最可靠）
    if '__file__' in globals():
        # scripts/validate_links.py -> skills/{skill_name}/
        script_path = Path(__file__).resolve()
        # scripts/validate_links.py -> scripts/ -> {skill_name}/
        skill_root = script_path.parents[1]
        # 验证是否是有效的技能目录（包含 SKILL.md）
        if (skill_root / "SKILL.md").exists():
            return skill_root

    # 方法2：通过环境变量定位（备用方案，支持自定义安装路径）
    env_skill_path = os.environ.get('VALIDATE_MD_REF Skill_PATH')
    if env_skill_path:
        skill_root = Path(env_skill_path).resolve()
        if (skill_root / "SKILL.md").exists():
            return skill_root

    # 方法3：尝试从常见安装路径定位（回退方案）
    # 依次检查：用户级技能目录、项目级技能目录
    possible_paths = [
        Path.home() / ".claude" / "skills" / "validate-md-ref",
        Path.home() / ".codex" / "skills" / "validate-md-ref",
        Path.cwd() / ".claude" / "skills" / "validate-md-ref",
    ]

    for path in possible_paths:
        if (path / "SKILL.md").exists():
            return path.resolve()

    # 方法4：如果都失败了，抛出错误并提供有用的诊断信息
    raise RuntimeError(
        f"无法定位 validate-md-ref 技能根目录。\n"
        f"请确认技能已正确安装到 ~/.claude/skills/ 或 ~/.codex/skills/\n"
        f"当前工作目录: {Path.cwd()}\n"
        f"__file__: {globals().get('__file__', '未定义')}\n"
        f"环境变量 VALIDATE_MD_REF Skill_PATH: {env_skill_path or '未设置'}"
    )


# 预计算技能根目录（模块加载时执行一次）
_skill_root = None


def get_skill_root_cached() -> Path:
    """获取技能根目录（带缓存，避免重复计算）"""
    global _skill_root
    if _skill_root is None:
        _skill_root = get_skill_root()
    return _skill_root


def get_config_path() -> Path:
    """获取默认配置文件的绝对路径"""
    return get_skill_root_cached() / "config.yaml"


def validate_path(file_path: Path, base_dir: Path = None) -> bool:
    """
    验证文件路径是否安全（防止路径遍历攻击）

    注意：对于 URL 验证工具，允许验证任意可访问的文件，
    只需确保路径不包含明显的恶意模式（如 ../.. 逃逸）。

    Args:
        file_path: 用户指定的文件路径
        base_dir: 允许的基目录（默认为当前工作目录，但此处不强制限制）

    Returns:
        True 表示路径安全
    """
    try:
        # 规范化路径
        resolved = file_path.resolve()

        # 检查路径是否包含明显的路径遍历模式
        path_str = str(file_path)
        dangerous_patterns = ['../..', '../../', '..\\..']
        if any(pattern in path_str for pattern in dangerous_patterns):
            return False

        # 检查路径是否尝试访问系统敏感目录
        resolved_str = str(resolved)
        sensitive_paths = ['/etc/', '/sys/', '/proc/', 'C:\\Windows\\System32']
        if any(resolved_str.startswith(sensitive) for sensitive in sensitive_paths):
            return False

        # 确保文件存在
        if not resolved.exists():
            return False

        return True
    except Exception:
        return False


def _curl_probe(url: str, timeout: int, method: str) -> tuple[int, str]:
    cmd = ['curl', '-s', '-L', '-o', os.devnull, '-w', '%{http_code}\n%{url_effective}']
    if method == 'HEAD':
        cmd.append('-I')
    else:
        cmd.extend(['--range', '0-0'])
    cmd.extend(['--', url])
    output = subprocess.check_output(
        cmd,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=timeout,
    ).strip().split('\n')
    if not output or not output[0].isdigit():
        raise ValueError(f"无法解析 curl 响应: {output}")
    return int(output[0]), output[1] if len(output) > 1 and output[1] else url


def validate_url(url: str, timeout: int = 10) -> Dict[str, any]:
    """
    验证单个 URL 的可达性

    Args:
        url: 要验证的 URL
        timeout: 超时时间（秒）

    Returns:
        包含验证结果的字典：
        {
            'url': str,
            'valid': bool,
            'status_code': int,
            'redirected': bool,
            'final_url': str,
            'error': str
        }
    """
    result = {
        'url': url,
        'valid': False,
        'status_code': None,
        'redirected': False,
        'final_url': url,
        'error': None
    }

    # 安全验证：确保 URL 格式合法，不包含 curl 选项
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            result['error'] = 'URL 格式非法'
            return result
        if parsed.scheme not in ['http', 'https']:
            result['error'] = '不支持的协议'
            return result
        # 检查 URL 是否包含可疑的 curl 选项特征
        if '--' in url or url.startswith('-'):
            result['error'] = 'URL 包含非法字符'
            return result
    except Exception as e:
        result['error'] = f'URL 解析失败: {e}'
        return result

    try:
        status_code, final_url = _curl_probe(url, timeout, 'HEAD')
        if status_code in (403, 405):
            status_code, final_url = _curl_probe(url, timeout, 'GET')
        result['status_code'] = status_code
        result['final_url'] = final_url
        result['redirected'] = final_url != url
        if 200 <= status_code < 400:
            result['valid'] = True
        else:
            result['error'] = f"HTTP {status_code}"

    except subprocess.CalledProcessError as e:
        result['error'] = f"执行失败: {e}"
    except subprocess.TimeoutExpired:
        result['error'] = f"超时（>{timeout}秒）"
    except Exception as e:
        result['error'] = str(e)

    return result


def _markdown_anchor_ids(content: str) -> set[str]:
    anchors = set()
    for match in re.finditer(r'<(?:a|span|div)\b[^>]*(?:id|name)=["\']([^"\']+)["\']', content, re.IGNORECASE):
        anchors.add(match.group(1))
    seen_headings: Dict[str, int] = {}
    for line in content.splitlines():
        match = re.match(r'^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$', line)
        if not match:
            continue
        heading = re.sub(r'<[^>]+>', '', match.group(1)).strip().lower()
        slug = re.sub(r'[^\w\- ]', '', heading, flags=re.UNICODE)
        slug = re.sub(r'[\s\-]+', '-', slug).strip('-')
        if not slug:
            continue
        count = seen_headings.get(slug, 0)
        anchors.add(slug if count == 0 else f"{slug}-{count}")
        seen_headings[slug] = count + 1
    return anchors


def validate_anchor(url: str, content: str) -> Dict[str, any]:
    anchor = unquote(url[1:])
    valid = anchor in _markdown_anchor_ids(content)
    return {
        'url': url,
        'valid': valid,
        'status_code': None,
        'redirected': False,
        'final_url': url,
        'error': None if valid else f'站内 anchor 不存在: {anchor}',
        'local_anchor': True,
    }


def extract_references(content: str) -> List[Dict[str, any]]:
    """
    从 Markdown 内容中提取引用

    Args:
        content: Markdown 文件内容

    Returns:
        引用列表，每个引用包含：
        {
            'index': int,           # 在文档中的位置
            'type': str,            # 引用类型
            'url': str,             # URL
            'text': str,            # 链接文本或描述
            'line_number': int,     # 行号
            'full_match': str       # 完整匹配的文本
        }
    """
    references = []

    # 引用模式
    patterns = [
        # 标准链接: [文本](URL)
        {
            'name': 'standard_link',
            'pattern': r'\[([^\]]+)\]\(([^)]+)\)'
        },
        # HTML <a> 标签: <a href="URL">文本</a> 或 <a href='URL'>文本</a>
        {
            'name': 'html_tag',
            'pattern': r'<a\s+href=(["\'])([^"\']+)\1[^>]*>(.*?)</a>'
        },
        # 参考文献样式: [编号]: URL "描述"
        {
            'name': 'bibliography',
            'pattern': r'^\[(\d+)\]:\s*(\S+)\s*"?(.*?)"?$'
        },
        # 脚注样式: [^编号]: URL "描述"
        {
            'name': 'footnote',
            'pattern': r'^\^\[(\d+)\]:\s*(\S+)\s*"?(.*?)"?$'
        }
    ]

    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        for pattern_info in patterns:
            pattern = pattern_info['pattern']
            type_name = pattern_info['name']

            if type_name in ('standard_link', 'html_tag'):
                # 标准链接和 HTML 标签可能一行有多个
                matches = re.finditer(pattern, line, re.IGNORECASE if type_name == 'html_tag' else 0)
                for match in matches:
                    url = match.group(2).strip()
                    text = match.group(1).strip() if type_name == 'standard_link' else match.group(3).strip()
                    references.append({
                        'index': len(references),
                        'type': type_name,
                        'url': url,
                        'text': text,
                        'line_number': line_num,
                        'full_match': match.group(0)
                    })
            else:
                # 参考文献样式每行最多一个
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    ref_num = match.group(1)
                    url = match.group(2).strip()
                    desc = match.group(3).strip() if len(match.groups()) >= 3 else ''

                    references.append({
                        'index': len(references),
                        'type': type_name,
                        'reference_number': ref_num,
                        'url': url,
                        'text': desc,
                        'line_number': line_num,
                        'full_match': match.group(0)
                    })

    return references


def should_skip_domain(url: str, whitelist: List[str], blacklist: List[str]) -> bool:
    """
    检查 URL 是否应该被跳过（基于域名白名单/黑名单）

    Args:
        url: 要检查的 URL
        whitelist: 域名白名单
        blacklist: 域名黑名单

    Returns:
        True 表示应该跳过验证
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # 检查黑名单
        for blocked in blacklist:
            if blocked.startswith('*.'):
                # 通配符匹配
                suffix = blocked[2:]
                if domain.endswith(suffix):
                    return True
            else:
                if domain == blocked.lower():
                    return True

        # 检查白名单
        if whitelist:
            allowed = False
            for allowed_domain in whitelist:
                if domain == allowed_domain.lower() or domain.endswith('.' + allowed_domain.lower()):
                    allowed = True
                    break
            return not allowed

        return False
    except Exception:
        return False


def validate_references(references: List[Dict], config: Dict, content: str = '') -> List[Dict]:
    """
    批量验证引用

    Args:
        references: 引用列表
        config: 配置字典

    Returns:
        包含验证结果的引用列表
    """
    results = []

    whitelist = config.get('domain_whitelist', [])
    blacklist = config.get('domain_blacklist', [])
    timeout = config.get('validation', {}).get('timeout', 10)

    for ref in references:
        url = ref['url']

        if url.startswith('#'):
            results.append({**ref, 'validation': validate_anchor(url, content)})
            continue

        # 检查是否应该跳过
        if should_skip_domain(url, whitelist, blacklist):
            results.append({
                **ref,
                'validation': {
                    'skipped': True,
                    'reason': '域名在黑名单或不在白名单中'
                }
            })
            continue

        # 验证 URL
        validation = validate_url(url, timeout)
        results.append({
            **ref,
            'validation': validation
        })

    return results


def generate_summary(results: List[Dict]) -> Dict:
    """
    生成验证结果摘要

    Args:
        results: 验证结果列表

    Returns:
        摘要统计信息
    """
    total = len(results)
    valid = sum(1 for r in results if r.get('validation', {}).get('valid', False))
    invalid = sum(1 for r in results if not r.get('validation', {}).get('valid', False) and not r.get('validation', {}).get('skipped', False))
    skipped = sum(1 for r in results if r.get('validation', {}).get('skipped', False))

    return {
        'total': total,
        'valid': valid,
        'invalid': invalid,
        'skipped': skipped,
        'valid_rate': f"{(valid / total * 100):.1f}%" if total > 0 else "0%"
    }


def _kernel_command() -> tuple[list[str], dict[str, str]]:
    """Resolve the public kernel command, with a source-tree fallback for development."""
    executable = shutil.which('bsk')
    if executable:
        probe = subprocess.run([executable, '--help'], capture_output=True, text=True, check=False)
        if probe.returncode == 0 and 'verification' in probe.stdout:
            return [executable], os.environ.copy()

    kernel_src = Path(__file__).resolve().parents[4] / 'packages' / 'bensz-skill-kernel' / 'src'
    env = os.environ.copy()
    env['PYTHONPATH'] = str(kernel_src) + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    return [sys.executable, '-m', 'bensz_skill_kernel.cli'], env


def record_runtime_events(events_path: str, results: List[Dict], gate: Dict, request_id: str, attempt_id: str = 'default') -> Dict:
    """Compatibility helper for callers that already have normalized results."""
    command, env = _kernel_command()
    result_payload = [{**item, 'request_id': request_id} for item in results]
    gate_payload = {**gate, 'request_id': request_id}
    args = command + [
        'verification', events_path,
        '--result-json', json.dumps(result_payload, ensure_ascii=False, separators=(',', ':')),
        '--gate-json', json.dumps(gate_payload, ensure_ascii=False, separators=(',', ':')),
        '--scope', 'skill',
        '--actor', 'validate-md-ref',
        '--attempt-id', attempt_id,
        '--idempotency-key', request_id,
    ]
    completed = subprocess.run(args, capture_output=True, text=True, env=env, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or 'bsk verification failed'
        raise RuntimeError(detail)
    return {'recorded': True, 'events': json.loads(completed.stdout)}


def run_kernel_verifier(args) -> int:
    """Explain that generic citation verification needs normalized evidence."""
    print(json.dumps({
        'error': 'citation.truth-and-fit requires normalized subject_context, source_metadata and source_excerpt evidence; use this Markdown adapter without --kernel mode',
    }, ensure_ascii=False))
    return 2
    command, env = _kernel_command()
    cmd = command + ['verifier', 'run', 'citation.truth-and-fit', '--version', '1.0.0', '--input', str(Path(args.markdown_file).resolve())]
    if args.config_file:
        try:
            import yaml
            config = yaml.safe_load(Path(args.config_file).read_text(encoding='utf-8')) or {}
            timeout = config.get('validation', {}).get('timeout')
            if timeout is not None:
                cmd.extend(['--timeout', str(int(timeout))])
            for domain in config.get('domain_blacklist', []) or []:
                cmd.extend(['--blacklist', str(domain)])
            for domain in config.get('domain_whitelist', []) or []:
                cmd.extend(['--whitelist', str(domain)])
        except (ImportError, OSError, ValueError) as exc:
            print(json.dumps({'error': f'加载配置失败: {exc}'}, ensure_ascii=False))
            return 1
    if args.events:
        cmd.extend(['--events', args.events])
    if args.run_id:
        cmd.extend(['--run-id', args.run_id])
    if args.attempt_id:
        cmd.extend(['--attempt-id', args.attempt_id])
    completed = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)
    if completed.stdout:
        print(completed.stdout, end='' if completed.stdout.endswith('\n') else '\n')
    if completed.returncode != 0 and completed.stderr:
        print(completed.stderr, file=sys.stderr, end='' if completed.stderr.endswith('\n') else '\n')
    return completed.returncode


def main(argv=None):
    """主函数"""
    parser = argparse.ArgumentParser(description='验证 Markdown 引用并输出结构化结果')
    parser.add_argument('markdown_file')
    parser.add_argument('config_file', nargs='?')
    parser.add_argument('--events', help='通过 bsk verifier run 追加到指定 events.ndjson')
    parser.add_argument('--run-id', help='本次验证的稳定运行 ID')
    parser.add_argument('--attempt-id', default='default')
    parser.add_argument('--legacy-local', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if not args.markdown_file:
        print(json.dumps({
            'error': '用法: validate_links.py <markdown_file> [config_file]'
        }))
        return 1

    md_file = Path(args.markdown_file)

    # 路径安全验证（防止路径遍历攻击）
    if not validate_path(md_file):
        print(json.dumps({
            'error': f'路径不安全或超出允许范围: {md_file}'
        }))
        return 1

    if not md_file.exists():
        print(json.dumps({
            'error': f'文件不存在: {md_file}'
        }))
        return 1

    # 读取 Markdown 内容
    content = md_file.read_text(encoding='utf-8')

    # 提取引用
    references = extract_references(content)

    # 加载配置（自动使用默认配置或用户指定的配置）
    config = {}
    config_path = None

    if args.config_file:
        # 用户提供了配置文件路径
        config_path = Path(args.config_file)
    else:
        # 自动使用技能默认配置文件
        try:
            config_path = get_config_path()
        except RuntimeError as e:
            # 无法定位技能根目录时，使用空配置（不影响基本功能）
            config = {}
            config_path = None

    # 只有在配置文件路径存在时才加载
    if config_path:
        try:
            import yaml
        except ImportError:
            print(json.dumps({
                'error': '未安装 yaml 库，请先安装：pip install pyyaml'
            }))
            return 1

        try:
            if not config_path.exists():
                print(json.dumps({
                    'error': f'配置文件不存在: {config_path}'
                }))
                return 1

            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            print(json.dumps({
                'error': f'加载配置失败: {e}'
            }))
            return 1

    # 验证引用
    results = validate_references(references, config, content)

    # 生成摘要
    summary = generate_summary(results)

    # 输出结果
    output = {
        'file': str(md_file),
        'summary': summary,
        'references': results,
    }

    # The Markdown parser is an adapter. The verifier itself is format-agnostic
    # and receives normalized claim/source evidence instead of a Markdown file.
    try:
        Evidence, VerificationRequest, VerifierRunner, build_builtin_registry = _load_verifier_runtime()
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        request_id = args.run_id or f"markdown:{content_hash[:16]}"
        request = VerificationRequest(
            subject={'type': 'citation', 'source_format': 'markdown', 'path': str(md_file), 'content_hash': content_hash},
            requirements=('citation.semantic_review',),
            evidence=(
                Evidence('subject_context', 'markdown', {'path': str(md_file), 'content': content}),
                Evidence('source_metadata', 'citation-list', {'references': results}),
                Evidence('source_excerpt', 'validator', {'summary': summary, 'references': results}),
            ),
            request_id=request_id,
        )
        verifier_results, gate = VerifierRunner(build_builtin_registry()).run(request, 'citation.truth-and-fit', version='1.0.0')
        output['verification'] = {
            'request_id': request.request_id,
            'results': [item.to_dict() for item in verifier_results],
            'gate': gate.to_dict(),
        }
    except Exception as exc:
        output['verification'] = {
            'results': [],
            'gate': {'decision': 'unchecked', 'reason': f'kernel unavailable: {exc}'},
        }

    if args.events and output.get('verification', {}).get('results'):
        try:
            output['runtime'] = record_runtime_events(
                args.events,
                output['verification']['results'],
                output['verification']['gate'],
                request_id,
                args.attempt_id,
            )
        except Exception as exc:
            output['runtime'] = {'recorded': False, 'error': str(exc)}
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return 2

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
