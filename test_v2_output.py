#!/usr/bin/env python3
"""
测试 V2 prompt 的实际输出
"""

import os
import json
import sys
from dotenv import load_dotenv
from openai import OpenAI
from httpx import Timeout

sys.path.insert(0, os.path.dirname(__file__))
from prompt import construct_prompt
from template import parse_output

load_dotenv()

# 加载第一个任务
with open('val.jsonl', 'r') as f:
    task = json.loads(f.readline())

# 生成 V2 prompt
messages = construct_prompt(task, version=2)

print("=" * 60)
print("V2 Prompt 测试 - 第一个任务")
print("=" * 60)

# 调用 API
api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
timeout = int(os.getenv("API_TIMEOUT_SECONDS", "60"))
max_tokens = int(os.getenv("API_MAX_TOKENS", "1000"))

try:
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=Timeout(timeout))
    
    print(f"调用 API...")
    print(f"  超时: {timeout}s")
    print(f"  最大 tokens: {max_tokens}")
    print()
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=1.0,
        max_tokens=max_tokens
    )
    
    reply_text = response.choices[0].message.content
    
    print("API 响应:")
    print("-" * 60)
    print(reply_text)
    print("-" * 60)
    print()
    
    # 尝试解析输出
    predicted_grid = parse_output(reply_text)
    
    print("解析结果:")
    print(f"  预测网格: {predicted_grid}")
    print(f"  网格是否为空: {len(predicted_grid) == 0}")
    print()
    
    # 获取真实答案
    ground_truth = task['test'][0]['output']
    print(f"真实答案: {ground_truth}")
    print(f"是否匹配: {predicted_grid == ground_truth}")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
