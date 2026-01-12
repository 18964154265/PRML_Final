#!/usr/bin/env python3
"""
快速测试脚本 - 验证性能优化配置
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("性能配置检查")
print("=" * 60)

# 检查关键配置
configs = {
    "API_TIMEOUT_SECONDS": ("60", "API 超时时间（秒）"),
    "API_MAX_TOKENS": ("1000", "最大响应 tokens"),
    "FAST_MODE": ("0", "快速模式（0=关闭, 1=开启）"),
    "PROMPT_VERSION": ("1", "提示词版本（1-5）"),
    "NUM_SAMPLES_V3": ("5", "V3 采样次数"),
}

print("\n当前配置:")
print("-" * 60)

config_dict = {}
for key, (default, desc) in configs.items():
    value = os.getenv(key, default)
    config_dict[key] = value
    status = "✓" if value != default else "○"
    print(f"{status} {key:25} = {value:10} ({desc})")

print("\n性能预测:")
print("-" * 60)

try:
    prompt_version = int(config_dict["PROMPT_VERSION"])
    fast_mode = int(config_dict["FAST_MODE"])
    num_samples = int(config_dict["NUM_SAMPLES_V3"])
    
    task_count = 5 if fast_mode else 30
    
    # API 调用次数预估
    api_calls_per_task = {
        1: 1,   # V1: 简单
        2: 1,   # V2: CoT
        3: num_samples,  # V3: 多采样
        4: 1,   # V4: 代码生成
        5: 3,   # V5: 链式推理
    }
    
    calls_per_task = api_calls_per_task.get(prompt_version, 1)
    total_calls = task_count * calls_per_task
    
    # 时间预估（每个 API 调用约 3-5 秒）
    time_per_call_min = 3
    time_per_call_max = 5
    total_time_min = total_calls * time_per_call_min
    total_time_max = total_calls * time_per_call_max
    
    version_names = {1: "简单", 2: "CoT", 3: "自洽投票", 4: "代码生成", 5: "链式推理"}
    version_name = version_names.get(prompt_version, "未知")
    
    print(f"  版本: V{prompt_version} ({version_name})")
    print(f"  任务数: {task_count}")
    print(f"  每任务 API 调用: {calls_per_task}")
    print(f"  总 API 调用: {total_calls}")
    print(f"  预估耗时: {total_time_min//60}m{total_time_min%60}s - {total_time_max//60}m{total_time_max%60}s")
    
    if total_calls >= 150:
        print("\n  ⚠️  警告: 大量 API 调用可能导致较长的运行时间")
        print("     建议: 减少 NUM_SAMPLES_V3 或使用更简单的版本")
    
except ValueError as e:
    print(f"  配置错误: {e}")

print("\n导入检查:")
print("-" * 60)

try:
    import openai
    print("✓ OpenAI 库已安装 (v" + openai.__version__ + ")")
except ImportError:
    print("✗ OpenAI 库未安装: pip install openai")
except AttributeError:
    print("✓ OpenAI 库已安装")

try:
    import httpx
    print("✓ httpx 库已安装")
except ImportError:
    print("✗ httpx 库未安装: pip install httpx")

try:
    import dotenv
    print("✓ python-dotenv 库已安装")
except ImportError:
    print("✗ python-dotenv 库未安装: pip install python-dotenv")

print("\n快速开始:")
print("-" * 60)
print("1. 快速验证（5 个任务）:")
print("   FAST_MODE=1 python test_prompt.py")
print("\n2. 标准运行（所有 30 个任务）:")
print("   python test_prompt.py")
print("\n3. 自定义配置:")
print("   API_TIMEOUT_SECONDS=30 API_MAX_TOKENS=500 python test_prompt.py")
print("=" * 60)
