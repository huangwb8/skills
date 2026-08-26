"""Small, dependency-free verifier packs shipped with the kernel.

Skills select these by stable id and tags.  Domain-specific packs can still be
registered by a Skill, but common packs live here so Skills do not duplicate
command, result, or Gate plumbing.
"""

from __future__ import annotations

import hashlib
import ipaddress
import re
import socket
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .verifiers import Evidence, PackRegistry, VerifierPack, VerifierSpec


_MAX_REDIRECTS = 5


def _anchor_ids(content: str) -> set[str]:
    anchors: set[str] = set()
    for match in re.finditer(r'<(?:a|span|div)\b[^>]*(?:id|name)=["\']([^"\']+)', content, re.IGNORECASE):
        anchors.add(match.group(1))
    seen: dict[str, int] = {}
    for line in content.splitlines():
        match = re.match(r'^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$', line)
        if not match:
            continue
        heading = re.sub(r'<[^>]+>', '', match.group(1)).strip().lower()
        slug = re.sub(r'[^\w\- ]', '', heading, flags=re.UNICODE)
        slug = re.sub(r'[\s\-]+', '-', slug).strip('-')
        if slug:
            count = seen.get(slug, 0)
            anchors.add(slug if count == 0 else f'{slug}-{count}')
            seen[slug] = count + 1
    return anchors


def _extract_references(content: str) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    patterns = (
        ('standard_link', re.compile(r'\[([^\]]+)\]\(([^)]+)\)')),
        ('html_tag', re.compile(r'<a\s+href=(["\'])([^"\']+)\1[^>]*>(.*?)</a>', re.IGNORECASE)),
    )
    for line_number, line in enumerate(content.splitlines(), 1):
        for type_name, pattern in patterns:
            for match in pattern.finditer(line):
                url = match.group(2).strip().split(' "', 1)[0]
                text = match.group(1).strip() if type_name == 'standard_link' else match.group(3).strip()
                references.append({'index': len(references), 'type': type_name, 'url': url, 'text': text, 'line_number': line_number, 'full_match': match.group(0)})
    return references


def _blocked(url: str, blacklist: tuple[str, ...]) -> bool:
    parsed = urlparse(url)
    hostname = (parsed.hostname or '').lower().rstrip('.')
    if hostname in {'localhost', '127.0.0.1', '::1', '0.0.0.0'} or hostname.endswith('.local') or hostname.endswith('.internal'):
        return True
    if any(hostname == item or (item.startswith('*.') and hostname.endswith(item[1:])) for item in blacklist):
        return True
    try:
        addresses = socket.getaddrinfo(hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        return any(
            address.is_private or address.is_loopback or address.is_link_local or address.is_reserved
            for item in addresses
            for address in (ipaddress.ip_address(item[4][0]),)
        )
    except (OSError, ValueError):
        return False


def _skip_reason(url: str, blacklist: tuple[str, ...], whitelist: tuple[str, ...]) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        return 'URL 格式非法或协议不受支持'
    hostname = (parsed.hostname or '').lower().rstrip('.')
    if whitelist and not any(hostname == item.lower().lstrip('*.') or hostname.endswith('.' + item.lower().lstrip('*.')) for item in whitelist):
        return '域名不在白名单中'
    if _blocked(url, blacklist):
        return '本地、回环或内部域名'
    return None


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _request_with_checked_redirects(url: str, method: str, timeout: int, blacklist: tuple[str, ...], whitelist: tuple[str, ...], opener: Any) -> tuple[int | None, str, str | None]:
    current_url = url
    for _ in range(_MAX_REDIRECTS + 1):
        headers = {'User-Agent': 'bensz-skill-kernel/0.3'}
        if method == 'GET':
            headers['Range'] = 'bytes=0-0'
        request = Request(current_url, method=method, headers=headers)
        try:
            with opener.open(request, timeout=timeout) as response:
                status = int(response.status)
        except HTTPError as exc:
            status = exc.code
            location = exc.headers.get('Location') if exc.headers else None
        else:
            location = None

        if 300 <= status < 400 and location:
            next_url = urljoin(current_url, location)
            if _skip_reason(next_url, blacklist, whitelist):
                return None, next_url, '重定向目标不在允许范围内'
            current_url = next_url
            continue
        return status, current_url, None
    return None, current_url, f'重定向次数超过限制（>{_MAX_REDIRECTS}）'


def _probe(url: str, timeout: int, blacklist: tuple[str, ...], whitelist: tuple[str, ...], *, opener: Any | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {'url': url, 'valid': False, 'status_code': None, 'redirected': False, 'final_url': url, 'error': None}
    initial_skip_reason = _skip_reason(url, blacklist, whitelist)
    if initial_skip_reason:
        if initial_skip_reason == 'URL 格式非法或协议不受支持':
            result['error'] = initial_skip_reason
        else:
            result['skipped'] = True
            result['reason'] = initial_skip_reason
        return result
    opener = opener or build_opener(_NoRedirectHandler())
    try:
        status, final_url, redirect_error = _request_with_checked_redirects(url, 'HEAD', timeout, blacklist, whitelist, opener)
        if redirect_error:
            result.update(final_url=final_url, redirected=final_url != url, skipped=True, reason=redirect_error)
            return result
        if status in {403, 405}:
            status, final_url, redirect_error = _request_with_checked_redirects(url, 'GET', timeout, blacklist, whitelist, opener)
            if redirect_error:
                result.update(final_url=final_url, redirected=final_url != url, skipped=True, reason=redirect_error)
                return result
        result.update(status_code=status, final_url=final_url, redirected=final_url != url, valid=200 <= status < 400)
        if not result['valid']:
            result['error'] = f'HTTP {status}'
    except (URLError, TimeoutError, OSError) as exc:
        result['error'] = str(exc)
    return result


def collect_markdown(path: str | Path, *, timeout: int = 10, blacklist: tuple[str, ...] = (), whitelist: tuple[str, ...] = ()) -> dict[str, Any]:
    target = Path(path).expanduser().resolve()
    if not target.is_file():
        raise ValueError(f'Markdown file does not exist: {path}')
    content = target.read_text(encoding='utf-8')
    anchors = _anchor_ids(content)
    references = _extract_references(content)
    collected: list[dict[str, Any]] = []
    for reference in references:
        url = reference['url']
        if url.startswith('#'):
            anchor = unquote(url[1:])
            validation = {'url': url, 'valid': anchor in anchors, 'local_anchor': True, 'error': None if anchor in anchors else f'站内 anchor 不存在: {anchor}'}
        else:
            validation = _probe(url, timeout, blacklist, whitelist)
        collected.append({**reference, 'validation': validation})
    total = len(collected)
    valid = sum(1 for item in collected if item['validation'].get('valid', False))
    skipped = sum(1 for item in collected if item['validation'].get('skipped', False))
    summary = {'total': total, 'valid': valid, 'invalid': total - valid - skipped, 'skipped': skipped, 'valid_rate': f'{valid / total * 100:.1f}%' if total else '0%'}
    return {'path': str(target), 'content_hash': hashlib.sha256(content.encode('utf-8')).hexdigest(), 'summary': summary, 'references': collected}


CITATION_TRUTH_FIT_SPEC = VerifierSpec(
    verifier_id='citation.truth-and-fit',
    version='1.0.0',
    mode='hybrid',
    capabilities=('evidence.identity', 'semantic.entailment', 'semantic.appropriateness'),
    evidence_requirements=('subject_context', 'source_metadata', 'source_excerpt'),
    uncertainty_policy={'missing_evidence': 'manual_review', 'engine_unavailable': 'unchecked'},
    tags=('common', 'citation', 'semantic', 'evidence'),
    metadata={'side_effects': 'none', 'requires_external_engine': True},
)


def _markdown_rule(request: Any, evidence: Mapping[str, Evidence]) -> Mapping[str, Any]:
    payload = evidence['reference.results'].content
    summary = dict(payload.get('summary', {}))
    findings = [
        {'id': 'unreachable-reference', 'severity': 'required', 'verdict': 'fail', 'message': item.get('validation', {}).get('error'), 'evidence_refs': [f"reference:{item.get('index')}"]}
        for item in payload.get('references', [])
        if item.get('validation', {}).get('valid') is False and not item.get('validation', {}).get('skipped')
    ]
    return {'verdict': 'fail' if findings else 'pass', 'facts': {'summary': summary}, 'findings': findings, 'evidence_refs': ['reference.results']}


def _citation_engine_gap(request: Any, evidence: Mapping[str, Evidence]) -> Mapping[str, Any]:
    return {
        'execution_status': 'unchecked',
        'verdict': 'unchecked',
        'uncertainty_reason': 'semantic citation engine is not bundled with the kernel',
        'evidence_refs': ['subject_context', 'source_metadata', 'source_excerpt'],
        'model_or_engine': 'none',
    }


def _file_exists(request: Any, evidence: Mapping[str, Evidence]) -> Mapping[str, Any]:
    path = request.subject.get('path')
    exists = bool(path and Path(path).is_file())
    return {'verdict': 'pass' if exists else 'fail', 'facts': {'path': path, 'exists': exists}, 'findings': [] if exists else [{'id': 'missing-file', 'severity': 'required', 'verdict': 'fail', 'message': f'file does not exist: {path}'}]}


FILE_SPEC = VerifierSpec(
    verifier_id='artifact.file-exists',
    version='1.0.0',
    mode='rule',
    capabilities=('filesystem.read',),
    tags=('common', 'filesystem', 'deterministic'),
    metadata={'side_effects': 'none'},
)


def build_builtin_registry() -> PackRegistry:
    registry = PackRegistry()
    registry.register(VerifierPack(FILE_SPEC, rules=(('file-exists', _file_exists),)))
    registry.register(VerifierPack(CITATION_TRUTH_FIT_SPEC, prompts=(('citation-semantics', _citation_engine_gap),)))
    return registry
