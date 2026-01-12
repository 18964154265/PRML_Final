#!/usr/bin/env python3
"""
V2 诊断脚本 - 测试前 5 个任务
"""

import os
import json
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))

from openai import OpenAI
from httpx import Timeout
from prompt import construct_prompt
from template import parse_output

load_dotenv()

# 加载数据
with open('val.jsonl', 'r') as f:
    data = [json.loads(line) for i, line in enumerate(f) if i < 5]

print("=" * 70)
print(f"V2 诊断测试 - 前 {len(data)} 个任务")
print("=" * 70)

api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
timeout = int(os.getenv("API_TIMEOUT_SECONDS", "60"))
max_tokens = int(os.getenv("API_MAX_TOKENS", "1000"))

client = OpenAI(api_key=api_key, base_url=base_url, timeout=Timeout(timeout))

correct = 0
empty_outputs = 0

for idx, task in enumerate(data):
    print(f"\n[{idx+1}/{len(data)}] 任务处理中...")
    
    try:
        # 生成 V2 prompt
        messages = construct_prompt(task, version=2)
        
        # 调用 API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=1.0,
            max_tokens=max_tokens
        )
        
        reply_text = response.choices[0].message.content
        
        # 解析输出
        predicted_grid = parse_output(reply_text)
        
        # 获取真实答案
        ground_truth = task['test'][0]['output']
        
        # 检查结果
        is_correct = predicted_grid == ground_truth
        is_empty = len(predicted_grid) == 0
        
        if is_empty:
            empty_outputs += 1
            status = "✗ 空输出"
        elif is_correct:
            correct += 1
            status = "✓ 正确"
        else:
            status = "✗ 错误"
        
        print(f"  {status}")
        print(f"  预测形状: {len(predicted_grid)}x{len(predicted_grid[0]) if predicted_grid else 0}")
        print(f"  真实形状: {len(ground_truth)}x{len(ground_truth[0]) if ground_truth else 0}")
        
        if is_empty:
            print(f"  ⚠️  注意: 预测为空矩阵")
            print(f"  API 回复片段: {reply_text[:200]}...")
        
    except Exception as e:
        print(f"  ✗ 错误: {str(e)}")

print("\n" + "=" * 70)
print(f"统计结果:")
print(f"  正确: {correct}/{len(data)}")
print(f"  空输出: {empty_outputs}/{len(data)}")
print(f"  准确率: {100*correct/len(data):.1f}%")
print("=" * 70)

if empty_outputs > len(data) * 0.3:
    print("\n⚠️  警告: 空输出比例过高（>30%）")
    print("   可能原因:")
    print("   1. parse_output 提取失败")
    print("   2. 模型没有生成格式正确的输出")
    print("   3. max_tokens 太小导致输出被截断")
