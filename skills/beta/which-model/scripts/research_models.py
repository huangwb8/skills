#!/usr/bin/env python3
"""
research_models.py - 通过联网搜索调研模型最佳实践

功能：
1. 基于任务特征生成检索词
2. 使用 MCP 工具执行搜索
3. 收集并评分搜索结果
4. 输出 research_results.json
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


# MCP 工具优先级（通过环境变量或直接调用）
MCP_SEARCH_PRIORITY = [
    'tavily-search',
    'searxng_web_search',
    'search'  # DuckDuckGo
]


def generate_search_queries(task_features: Dict[str, Any], target_vendors: List[str] = None) -> List[str]:
    """基于任务特征生成检索词

    Args:
        task_features: 技能任务特征分析结果
        target_vendors: 目标模型厂商列表，默认为 ['Anthropic', 'OpenAI']
    """
    if target_vendors is None:
        target_vendors = ['Anthropic', 'OpenAI']

    queries = []

    task_types = task_features.get('task_types', [])
    complexity = task_features.get('complexity_level', 'medium')

    # 厂商特定模型名称映射
    vendor_models = {
        'Anthropic': ['Claude', 'Opus', 'Sonnet', 'Haiku'],
        'OpenAI': ['GPT-4', 'GPT-4o', 'o1', 'GPT'],
        'Google': ['Gemini', 'Gemini Pro', 'Gemini Ultra'],
        'Meta': ['Llama', 'Llama 2', 'Llama 3'],
        'Mistral': ['Mistral', 'Mixtral', 'Mistral Large'],
        'DeepSeek': ['DeepSeek', 'DeepSeek-V2', 'DeepSeek-Coder']
    }

    # 为每个厂商收集模型名称（每个厂商最多 2 个，避免查询过多）
    vendor_model_names = {}
    for vendor in target_vendors:
        if vendor in vendor_models:
            vendor_model_names[vendor] = vendor_models[vendor][:2]

    # 基础查询词模板（支持多厂商）
    query_templates = {
        '文本生成': [
            '{model} long text generation',
            '{model} writing best practice',
            '{model} content generation'
        ],
        '代码分析': [
            '{model} code analysis',
            '{model} code review',
            '{model} code understanding'
        ],
        '联网搜索': [
            '{model} web search',
            '{model} information retrieval'
        ],
        '数据处理': [
            '{model} data extraction',
            '{model} JSON processing',
            '{model} structured output'
        ],
        '多步骤推理': [
            '{model} complex reasoning',
            '{model} chain of thought',
            '{model} problem solving'
        ]
    }

    # 为每个任务类型和厂商组合生成查询
    for task_type in task_types:
        if task_type in query_templates:
            for template in query_templates[task_type]:
                for vendor in target_vendors:
                    if vendor in vendor_model_names:
                        for model_name in vendor_model_names[vendor]:
                            queries.append(template.format(model=model_name))

    # 添加模型对比查询（跨厂商）
    if len(target_vendors) > 1:
        vendor_pairs = []
        for i, vendor1 in enumerate(target_vendors):
            for vendor2 in target_vendors[i+1:]:
                vendor_pairs.append((vendor1, vendor2))

        for vendor1, vendor2 in vendor_pairs[:2]:  # 最多 2 组对比
            model1 = vendor_models.get(vendor1, [vendor1])[0]
            model2 = vendor_models.get(vendor2, [vendor2])[0]
            queries.append(f'{model1} vs {model2} comparison')
            queries.append(f'{model1} or {model2} which is better')

    # 添加通用参数查询（不特定于厂商）
    queries.extend([
        'LLM reasoning intensity best practice',
        'LLM temperature parameters guide',
        'when to use different LLM models'
    ])

    return list(set(queries))  # 去重


def search_with_mcp(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """使用 MCP 工具执行搜索"""
    results = []

    # 尝试按优先级使用 MCP 工具
    for tool_name in MCP_SEARCH_PRIORITY:
        try:
            # 这里需要实际的 MCP 工具调用
            # 以下是模拟实现，实际使用时需要集成真实的 MCP 工具
            print(f"Searching with {tool_name}: {query}")

            # 模拟搜索结果
            mock_results = [
                {
                    'title': f"Mock result for: {query}",
                    'url': f"https://example.com/{query.replace(' ', '-')}",
                    'snippet': f"Mock search result snippet about {query}",
                    'source': tool_name
                }
            ]

            results.extend(mock_results)
            break  # 成功后不再尝试其他工具

        except Exception as e:
            print(f"Failed to use {tool_name}: {e}")
            continue

    return results


def score_relevance(result: Dict[str, Any], query: str) -> float:
    """评分搜索结果的相关性（0-1）"""
    title = result.get('title', '').lower()
    snippet = result.get('snippet', '').lower()
    query_lower = query.lower()

    # 简单的关键词匹配评分
    score = 0.0

    query_words = set(query_lower.split())
    title_words = set(title.split())
    snippet_words = set(snippet.split())

    # 标题匹配权重更高
    title_match = len(query_words & title_words) / max(len(query_words), 1)
    snippet_match = len(query_words & snippet_words) / max(len(query_words), 1)

    score = title_match * 0.7 + snippet_match * 0.3

    return min(score, 1.0)


def research_models(skill_analysis: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
    """执行完整的模型调研流程"""
    if config is None:
        config = {}

    task_features = skill_analysis.get('task_features', {})
    max_results = config.get('research', {}).get('max_results_per_query', 10)
    relevance_threshold = config.get('research', {}).get('relevance_threshold', 0.6)
    target_vendors = config.get('research', {}).get('target_vendors', ['Anthropic', 'OpenAI'])

    # 1. 生成检索词（传入目标厂商）
    queries = generate_search_queries(task_features, target_vendors)

    # 2. 执行搜索
    all_results = []
    for query in queries:
        results = search_with_mcp(query, max_results)
        for result in results:
            result['query'] = query
            result['relevance_score'] = score_relevance(result, query)
        all_results.extend(results)

    # 3. 过滤低相关性结果
    filtered_results = [
        r for r in all_results
        if r['relevance_score'] >= relevance_threshold
    ]

    # 4. 排序
    filtered_results.sort(key=lambda x: x['relevance_score'], reverse=True)

    return {
        'timestamp': datetime.now().isoformat(),
        'skill_name': skill_analysis.get('skill_name'),
        'queries_used': queries,
        'total_results': len(all_results),
        'filtered_results': len(filtered_results),
        'results': filtered_results[:50]  # 限制返回数量
    }


def load_config(config_path: Path = None) -> Dict[str, Any]:
    """加载配置文件"""
    if config_path is None:
        # 默认使用 which-model 技能目录下的 config.yaml
        script_dir = Path(__file__).resolve().parents[1]
        config_path = script_dir / 'config.yaml'

    if not config_path.exists():
        return {}

    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        print("Warning: PyYAML not installed, using default config")
        return {}
    except Exception as e:
        print(f"Warning: Failed to load config from {config_path}: {e}")
        return {}


def main():
    if len(sys.argv) < 2:
        print("Usage: python research_models.py <skill_analysis.json> [config_path]")
        sys.exit(1)

    analysis_path = Path(sys.argv[1])
    config_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not analysis_path.exists():
        print(f"Error: Analysis file not found: {analysis_path}")
        sys.exit(1)

    try:
        # 加载配置
        config = load_config(config_path)

        with open(analysis_path, 'r', encoding='utf-8') as f:
            skill_analysis = json.load(f)

        # 显示使用的配置
        target_vendors = config.get('research', {}).get('target_vendors', ['Anthropic', 'OpenAI'])
        print(f"Target vendors: {', '.join(target_vendors)}")

        research_results = research_models(skill_analysis, config)

        # 保存到技能目录
        skill_dir = Path(analysis_path).parent
        output_path = skill_dir / 'research_results.json'

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(research_results, f, indent=2, ensure_ascii=False)

        print(f"Research complete. Results saved to: {output_path}")
        print(f"Found {research_results['filtered_results']} relevant results")
        print(f"Queries used: {len(research_results['queries_used'])}")

    except Exception as e:
        print(f"Error during research: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
