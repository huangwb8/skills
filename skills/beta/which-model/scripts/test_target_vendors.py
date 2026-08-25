#!/usr/bin/env python3
"""
test_target_vendors.py - 测试 target_vendors 参数功能

验证：
1. 默认厂商列表为 ['Anthropic', 'OpenAI']
2. 可以从 config.yaml 读取 target_vendors
3. generate_search_queries 正确使用 target_vendors
"""

import json
import sys
from pathlib import Path

# 添加 scripts 目录到路径
scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from research_models import generate_search_queries, load_config


def test_default_vendors():
    """测试默认厂商列表"""
    print("测试 1: 默认厂商列表")

    task_features = {
        'task_types': ['文本生成'],
        'complexity_level': 'medium'
    }

    queries = generate_search_queries(task_features)

    # 验证包含 Anthropic 和 OpenAI 的模型
    has_anthropic = any('Claude' in q or 'Opus' in q or 'Sonnet' in q for q in queries)
    has_openai = any('GPT' in q or 'GPT-4' in q for q in queries)

    assert has_anthropic, "应包含 Anthropic 模型名"
    assert has_openai, "应包含 OpenAI 模型名"

    print("✓ 默认厂商列表测试通过")
    print(f"  生成了 {len(queries)} 个查询")
    print(f"  示例查询: {queries[:3]}")
    return True


def test_custom_vendors():
    """测试自定义厂商列表"""
    print("\n测试 2: 自定义厂商列表")

    task_features = {
        'task_types': ['文本生成'],
        'complexity_level': 'medium'
    }

    # 仅 Anthropic
    queries_anthropic = generate_search_queries(task_features, ['Anthropic'])
    has_anthropic_only = any('Claude' in q or 'Opus' in q for q in queries_anthropic)
    has_no_openai = not any('GPT' in q for q in queries_anthropic)

    assert has_anthropic_only, "应包含 Anthropic 模型名"
    assert has_no_openai, "不应包含 OpenAI 模型名"

    print("✓ 仅 Anthropic 测试通过")
    print(f"  生成了 {len(queries_anthropic)} 个查询")

    # Anthropic + Google
    queries_mixed = generate_search_queries(task_features, ['Anthropic', 'Google'])
    has_google = any('Gemini' in q for q in queries_mixed)

    assert has_google, "应包含 Google 模型名"

    print("✓ Anthropic + Google 测试通过")
    print(f"  生成了 {len(queries_mixed)} 个查询")
    return True


def test_config_loading():
    """测试从 config.yaml 加载配置"""
    print("\n测试 3: 从 config.yaml 加载配置")

    config_path = Path(__file__).parent.parent / 'config.yaml'
    config = load_config(config_path)

    target_vendors = config.get('research', {}).get('target_vendors', [])

    assert len(target_vendors) > 0, "config.yaml 应定义 target_vendors"
    assert 'Anthropic' in target_vendors, "默认应包含 Anthropic"
    assert 'OpenAI' in target_vendors, "默认应包含 OpenAI"

    print("✓ config.yaml 加载测试通过")
    print(f"  配置的厂商: {', '.join(target_vendors)}")
    return True


def test_vendor_specific_models():
    """测试厂商特定模型名称映射"""
    print("\n测试 4: 厂商特定模型名称映射")

    task_features = {
        'task_types': ['文本生成'],
        'complexity_level': 'medium'
    }

    # 测试所有支持的厂商
    all_vendors = ['Anthropic', 'OpenAI', 'Google', 'Meta', 'Mistral', 'DeepSeek']

    queries = generate_search_queries(task_features, all_vendors)

    # 验证每个厂商的模型名都出现在查询中
    vendor_keywords = {
        'Anthropic': ['Claude', 'Opus'],
        'OpenAI': ['GPT'],
        'Google': ['Gemini'],
        'Meta': ['Llama'],
        'Mistral': ['Mistral'],
        'DeepSeek': ['DeepSeek']
    }

    for vendor, keywords in vendor_keywords.items():
        found = any(any(keyword in q for keyword in keywords) for q in queries)
        assert found, f"应包含 {vendor} 的模型名"
        print(f"  ✓ {vendor}: 已包含")

    print("✓ 厂商特定模型名称映射测试通过")
    return True


def test_cross_vendor_comparison():
    """测试跨厂商对比查询生成"""
    print("\n测试 5: 跨厂商对比查询生成")

    task_features = {
        'task_types': ['文本生成'],
        'complexity_level': 'medium'
    }

    # 多厂商应生成对比查询
    queries = generate_search_queries(task_features, ['Anthropic', 'OpenAI', 'Google'])

    has_comparison = any(
        'vs' in q or 'comparison' in q or 'which is better' in q
        for q in queries
    )

    assert has_comparison, "多厂商应生成对比查询"

    comparison_queries = [q for q in queries if 'vs' in q or 'comparison' in q]
    print(f"✓ 跨厂商对比查询测试通过")
    print(f"  对比查询数: {len(comparison_queries)}")
    print(f"  示例: {comparison_queries[:2]}")
    return True


def main():
    print("=" * 60)
    print("target_vendors 参数功能测试")
    print("=" * 60)

    tests = [
        test_default_vendors,
        test_custom_vendors,
        test_config_loading,
        test_vendor_specific_models,
        test_cross_vendor_comparison
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            failed += 1
            print(f"✗ 测试失败: {e}")
        except Exception as e:
            failed += 1
            print(f"✗ 测试错误: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"测试总结: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
