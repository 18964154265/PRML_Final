#!/usr/bin/env python3
"""
诊断脚本：测试 parse_output 函数和 V2 prompt
"""

import json
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from template import parse_output
from prompt import prompt_v2_fewshot_cot, construct_prompt

# 测试用例 1: 简单的网格输出
print("=" * 60)
print("测试 1: 简单 2x2 网格")
print("=" * 60)
test_text_1 = "OUTPUT: [[0, 1], [2, 3]]"
result_1 = parse_output(test_text_1)
print(f"输入: {test_text_1}")
print(f"输出: {result_1}")
print()

# 测试用例 2: 包含其他文本的网格
print("=" * 60)
print("测试 2: 包含详细推理的网格")
print("=" * 60)
test_text_2 = """
OBSERVATIONS: The input grid has colors that transform...
PATTERN RULE: Each cell is inverted...
REASONING: Applying this rule to the test...
OUTPUT: [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
"""
result_2 = parse_output(test_text_2)
print(f"输入: {test_text_2}")
print(f"输出: {result_2}")
print()

# 测试用例 3: 大型网格
print("=" * 60)
print("测试 3: 大型网格（5x5）")
print("=" * 60)
test_text_3 = "OUTPUT: [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9], [0, 1, 2, 3, 4], [5, 6, 7, 8, 9], [0, 1, 2, 3, 4]]"
result_3 = parse_output(test_text_3)
print(f"输入: {test_text_3}")
print(f"输出: {result_3}")
print()

# 测试用例 4: 多个数组（会选择第一个）
print("=" * 60)
print("测试 4: 多个可能的数组")
print("=" * 60)
test_text_4 = """
First attempt: [[1, 2], [3, 4]]
Second attempt: [[5, 6], [7, 8]]
FINAL OUTPUT: [[0, 1], [2, 3]]
"""
result_4 = parse_output(test_text_4)
print(f"输入: {test_text_4}")
print(f"输出: {result_4}")
print()

# 测试用例 5: 空输出
print("=" * 60)
print("测试 5: 没有有效数组的输出")
print("=" * 60)
test_text_5 = """
I'm unable to determine the pattern.
The output should be a grid but I cannot compute it.
"""
result_5 = parse_output(test_text_5)
print(f"输入: {test_text_5}")
print(f"输出: {result_5}")
print()

# 测试用例 6: 加载真实的数据
print("=" * 60)
print("测试 6: 加载真实数据并检查 V2 prompt")
print("=" * 60)
try:
    with open('val.jsonl', 'r') as f:
        data = json.loads(f.readline())
    
    print(f"任务 ID: {data.get('id', 'unknown')}")
    print(f"训练样本数: {len(data['train'])}")
    print(f"测试样本数: {len(data['test'])}")
    
    # 生成 V2 prompt
    messages = construct_prompt(data, version=2)
    
    # 打印系统消息
    print("\n系统消息:")
    print(messages[0]['content'][:200] + "...")
    
    # 打印用户消息的前 500 字符
    print("\n用户消息（前 500 字符）:")
    print(messages[1]['content'][:500] + "...")
    
except Exception as e:
    print(f"错误: {e}")
