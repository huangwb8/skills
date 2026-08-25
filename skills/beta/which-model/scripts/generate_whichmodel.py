#!/usr/bin/env python3
"""
generate_whichmodel.py - 生成 WHICHMODEL 小节

功能：
1. 从调研结果中提取结构化知识
2. 按 WHICHMODEL 模板组织内容
3. 生成 Markdown 格式的最佳实践小节
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def extract_knowledge(research_results: Dict[str, Any], skill_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """从搜索结果中提取结构化知识"""
    results = research_results.get('results', [])

    # 初始化知识结构
    knowledge = {
        'scenarios': [],
        'general_principles': [],
        'model_patterns': {
            'Opus': {'use_cases': [], 'typical_params': {}},
            'Sonnet': {'use_cases': [], 'typical_params': {}},
            'Haiku': {'use_cases': [], 'typical_params': {}}
        }
    }

    # 分析每个搜索结果
    for result in results:
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        url = result.get('url', '')
        text = f"{title} {snippet}".lower()

        # 识别模型使用场景
        if 'opus' in text and ('complex' in text or 'long' in text or 'quality' in text):
            knowledge['model_patterns']['Opus']['use_cases'].append({
                'scenario': title,
                'reason': snippet[:100],
                'source': url
            })

        if 'sonnet' in text and ('balanced' in text or 'code' in text):
            knowledge['model_patterns']['Sonnet']['use_cases'].append({
                'scenario': title,
                'reason': snippet[:100],
                'source': url
            })

        if 'haiku' in text and ('fast' in text or 'quick' in text or 'simple' in text):
            knowledge['model_patterns']['Haiku']['use_cases'].append({
                'scenario': title,
                'reason': snippet[:100],
                'source': url
            })

        # 识别通用原则
        if any(word in text for word in ['principle', 'best practice', 'guideline', 'recommend']):
            knowledge['general_principles'].append({
                'title': title,
                'content': snippet[:200],
                'source': url
            })

    return knowledge


def generate_scenarios(knowledge: Dict[str, Any], skill_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """基于知识和技能分析生成场景"""
    task_types = skill_analysis.get('task_features', {}).get('task_types', [])
    complexity = skill_analysis.get('task_features', {}).get('complexity_level', 'medium')

    scenarios = []

    # 基于任务类型生成场景
    scenario_map = {
        '文本生成': {
            'name': '长文本生成（综述/报告）',
            'model': 'Claude Opus 4.5',
            'reasoning': 'high',
            'thinking': True,
            'reason': '需要强推理能力确保内容连贯性和深度'
        },
        '代码分析': {
            'name': '代码分析与重构',
            'model': 'Claude Sonnet 4.5',
            'reasoning': 'medium',
            'thinking': False,
            'reason': '结构化思维适合代码分析，性价比高'
        },
        '联网搜索': {
            'name': '信息检索与综合',
            'model': 'Claude Sonnet 4.5',
            'reasoning': 'medium',
            'thinking': True,
            'reason': '需要综合多源信息但无需最强推理'
        },
        '数据处理': {
            'name': '数据提取与处理',
            'model': 'Claude Haiku 4.5',
            'reasoning': 'low',
            'thinking': False,
            'reason': '结构化任务，快速响应优先'
        }
    }

    for task_type in task_types:
        if task_type in scenario_map:
            scenarios.append(scenario_map[task_type])

    # 如果没有匹配场景，添加默认场景
    if not scenarios:
        scenarios.append({
            'name': '标准任务执行',
            'model': 'Claude Sonnet 4.5',
            'reasoning': 'medium',
            'thinking': False,
            'reason': '平衡性能与成本，适用于大多数任务'
        })

    return scenarios


def load_template(template_path: Path) -> str:
    """加载 WHICHMODEL 模板"""
    if not template_path.exists():
        # 返回默认模板
        return """## WHICHMODEL - 模型选择最佳实践

本节由 `which-model` skill 自动调研生成，最后更新：{timestamp}

{scenarios}

### 通用原则

{principles}

### 更新记录

- {timestamp}：初始生成
"""

    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def format_scenario(scenario: Dict[str, Any], index: int) -> str:
    """格式化单个场景"""
    return f"""### 场景{index}：{scenario['name']}

**典型使用场景**：基于技能任务特征分析得出

- **推荐模型**：{scenario['model']}
- **推荐参数**：
  - 推理强度：{scenario['reasoning']}
  - Thinking 模式：{'开' if scenario.get('thinking', False) else '关'}
  - Temperature：{scenario.get('temperature', '默认值')}
  - Max Tokens：{scenario.get('max_tokens', '按需设置')}
- **理由**：{scenario['reason']}
- **来源**：基于 {len(scenario.get('sources', []))} 个来源的调研分析

---"""


def generate_whichmodel_section(
    knowledge: Dict[str, Any],
    skill_analysis: Dict[str, Any],
    template_path: Path = None
) -> str:
    """生成 WHICHMODEL 小节"""
    timestamp = datetime.now().strftime('%Y-%m-%d')

    # 加载模板
    if template_path is None:
        template_path = Path(__file__).parent.parent / 'references' / 'WHICHMODEL_template.md'

    template = load_template(template_path)

    # 生成场景
    scenarios = generate_scenarios(knowledge, skill_analysis)
    scenarios_text = '\n\n'.join([
        format_scenario(s, i + 1)
        for i, s in enumerate(scenarios[:8])  # 最多 8 个场景
    ])

    # 生成通用原则
    principles = knowledge.get('general_principles', [])
    if not principles:
        # 默认原则
        principles_text = """1. **复杂度与模型匹配**
   - 高复杂度任务（多步骤推理、长文本生成）→ Claude Opus 4.5
   - 中等复杂度任务（代码分析、标准写作）→ Claude Sonnet 4.5
   - 简单任务（数据处理、快速响应）→ Claude Haiku 4.5

2. **成本效益平衡**
   - 优先尝试 Sonnet，在质量不足时升级到 Opus
   - 批量任务考虑使用 Haiku 降低成本

3. **参数调优**
   - 推理强度：质量优先用 high，速度优先用 low
   - Thinking 模式：复杂推理任务建议开启
   - Temperature：创造性任务可适当提高"""
    else:
        principles_text = '\n\n'.join([
            f"{i+1}. **{p.get('title', '原则')}**\n   {p.get('content', '')[:200]}"
            for i, p in enumerate(principles[:5])
        ])

    # 填充模板
    content = template.format(
        timestamp=timestamp,
        scenarios=scenarios_text,
        principles=principles_text,
       生成日期=timestamp,
        调研来源数量=len(principles),
        X=len(principles),
        YYYY_MM_DD=timestamp
    )

    return content


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_whichmodel.py <research_results.json> <skill_analysis.json>")
        sys.exit(1)

    research_path = Path(sys.argv[1])
    analysis_path = Path(sys.argv[2])

    if not research_path.exists() or not analysis_path.exists():
        print("Error: Input files not found")
        sys.exit(1)

    try:
        with open(research_path, 'r', encoding='utf-8') as f:
            research_results = json.load(f)

        with open(analysis_path, 'r', encoding='utf-8') as f:
            skill_analysis = json.load(f)

        # 提取知识
        knowledge = extract_knowledge(research_results, skill_analysis)

        # 生成 WHICHMODEL 小节
        whichmodel_section = generate_whichmodel_section(
            knowledge,
            skill_analysis
        )

        # 保存到文件
        skill_dir = Path(analysis_path).parent
        output_path = skill_dir / 'WHICHMODEL_section.md'

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(whichmodel_section)

        print(f"WHICHMODEL section generated: {output_path}")
        print(f"Section length: {len(whichmodel_section)} characters")

    except Exception as e:
        print(f"Error during generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
