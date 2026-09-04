#!/usr/bin/env python3
"""
score_sources.py - 硬编码的来源评分逻辑

功能：
1. 从 config.yaml 加载来源可信度配置
2. 计算每个搜索结果的综合得分
3. 应用营销倾向惩罚
4. 输出评分后的结果

设计原则：硬编码确保评分稳定性，不受 AI 自主规划影响
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
from urllib.parse import urlparse


def load_config(config_path: Path = None) -> Dict[str, Any]:
    """加载配置文件"""
    if config_path is None:
        config_path = Path(__file__).resolve().parents[1] / 'config.yaml'

    if not config_path.exists():
        return {}

    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Failed to load config: {e}")
        return {}


def get_domain_credibility_weight(url: str, config: Dict[str, Any]) -> float:
    """获取域名可信度权重（硬编码）"""
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return 0.5

    # 移除 www. 前缀
    if domain.startswith('www.'):
        domain = domain[4:]

    credibility_config = config.get('source_credibility', {})
    domain_weights = credibility_config.get('domain_weights', {})

    # 检查每个类别
    for category, data in domain_weights.items():
        if isinstance(data, dict) and 'domains' in data:
            if domain in data['domains']:
                return data.get('weight', 0.5)

    # 未知域名返回默认权重
    return credibility_config.get('unknown_domain_weight', 0.5)


def detect_marketing_bias(text: str, config: Dict[str, Any]) -> float:
    """检测营销倾向（硬编码）"""
    bias_config = config.get('bias_detection', {})

    # 获取关键词列表
    marketing_words = bias_config.get('marketing_words', {})
    positive_excess = marketing_words.get('positive_excess', [])
    absolute_words = marketing_words.get('absolute_words', [])
    balanced_indicators = bias_config.get('balanced_indicators', [])

    # 获取阈值
    marketing_threshold = bias_config.get('sentiment_thresholds', {}).get('marketing_too_positive', 3)
    absolute_threshold = bias_config.get('sentiment_thresholds', {}).get('absolute_excess', 2)

    text_lower = text.lower()

    # 统计过度正面词汇
    positive_count = sum(1 for word in positive_excess if word in text_lower)

    # 统计绝对化词语
    absolute_count = sum(1 for word in absolute_words if word in text_lower)

    # 统计平衡指标
    balanced_count = sum(1 for word in balanced_indicators if word in text_lower)

    # 计算营销倾向分数（0-1，越低表示营销倾向越强）
    marketing_score = 1.0

    # 过度正面惩罚
    if positive_count >= marketing_threshold and balanced_count == 0:
        marketing_score -= 0.4  # 严重营销倾向

    # 绝对化词语惩罚
    if absolute_count >= absolute_threshold and balanced_count == 0:
        marketing_score -= 0.3

    # 有平衡指标，奖励
    if balanced_count >= 2:
        marketing_score = min(marketing_score + 0.1, 1.0)

    return max(marketing_score, 0.0)


def calculate_impartial_score(
    result: Dict[str, Any],
    query: str,
    config: Dict[str, Any]
) -> float:
    """计算综合客观性评分（硬编码公式）"""
    scoring_config = config.get('scoring', {})

    # 获取权重
    formula = scoring_config.get('formula', {})
    relevance_weight = formula.get('relevance_weight', 0.30)
    credibility_weight = formula.get('credibility_weight', 0.50)
    neutrality_weight = formula.get('neutrality_weight', 0.20)

    # 1. 相关性评分（来自 research_models.py）
    relevance = result.get('relevance_score', 0.5)

    # 2. 可信度评分（基于域名）
    credibility = get_domain_credibility_weight(result.get('url', ''), config)

    # 3. 中立性评分（检测营销倾向）
    title_snippet = result.get('title', '') + ' ' + result.get('snippet', '')
    neutrality = detect_marketing_bias(title_snippet, config)

    # 综合评分（硬编码公式）
    final_score = (
        relevance * relevance_weight +
        credibility * credibility_weight +
        neutrality * neutrality_weight
    )

    return final_score


def score_research_results(
    research_results: Dict[str, Any],
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """对所有调研结果进行评分"""
    if config is None:
        config = load_config()

    results = research_results.get('results', [])

    # 为每个结果计算综合评分
    for result in results:
        query = result.get('query', '')
        result['impartial_score'] = calculate_impartial_score(result, query, config)

        # 添加评分详情（用于调试）
        title_snippet = result.get('title', '') + ' ' + result.get('snippet', '')
        result['score_details'] = {
            'relevance': result.get('relevance_score', 0.5),
            'credibility': get_domain_credibility_weight(result.get('url', ''), config),
            'neutrality': detect_marketing_bias(title_snippet, config)
        }

    # 按综合评分重新排序
    results.sort(key=lambda x: x['impartial_score'], reverse=True)

    # 过滤低分结果
    min_score = config.get('scoring', {}).get('min_acceptable_score', 0.4)
    filtered_results = [r for r in results if r['impartial_score'] >= min_score]

    return {
        'timestamp': research_results.get('timestamp'),
        'skill_name': research_results.get('skill_name'),
        'queries_used': research_results.get('queries_used'),
        'total_results': len(results),
        'filtered_results': len(filtered_results),
        'results': filtered_results[:50],  # 限制返回数量
        'scoring_method': 'hardcoded_formula_v1'  # 标记使用硬编码
    }


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python score_sources.py <research_results.json> [config_path]")
        sys.exit(1)

    research_path = Path(sys.argv[1])
    config_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not research_path.exists():
        print(f"Error: Research results file not found: {research_path}")
        sys.exit(1)

    try:
        # 加载配置
        config = load_config(config_path)

        # 加载调研结果
        with open(research_path, 'r', encoding='utf-8') as f:
            research_results = json.load(f)

        # 评分
        scored_results = score_research_results(research_results, config)

        # 保存
        output_path = research_path.parent / 'research_results_scored.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(scored_results, f, indent=2, ensure_ascii=False)

        print(f"✅ Scoring complete. Results saved to: {output_path}")
        print(f"📊 Filtered results: {scored_results['filtered_results']}/{scored_results['total_results']}")

        # 显示一些统计信息
        if scored_results['results']:
            avg_score = sum(r['impartial_score'] for r in scored_results['results']) / len(scored_results['results'])
            print(f"📈 Average impartial score: {avg_score:.2f}")

    except Exception as e:
        print(f"❌ Error during scoring: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
