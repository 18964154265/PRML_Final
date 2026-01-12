#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V2 空矩阵问题诊断和修复指南

问题: 在使用 V2 prompt 时，很多 predicted 都是空矩阵 []
原因: parse_output 函数无法正确提取模型输出中的网格
解决: 多层次改进 parse_output 和 V2 prompt
"""

# ============================================================================
# 问题描述
# ============================================================================
PROBLEM = """
使用 V2（Chain-of-Thought）版本时的现象:
- 很多任务的 predicted_grid 为 []（空矩阵）
- 表面上看是提取失败，实际上模型可能生成了正确的输出
- 正则表达式可能无法正确处理嵌套数组
"""

# ============================================================================
# 解决方案
# ============================================================================
SOLUTIONS = """
1. Improved parse_output function (template.py)
   - Added OUTPUT: tag priority extraction
   - Implemented manual bracket matching as fallback
   - Removed non-greedy matching in regex
   
2. Improved V2 Prompt (prompt.py)
   - System message clarifies OUTPUT must be valid 2D list
   - Emphasizes no text should follow OUTPUT:
   - Added clear format examples
   
3. Added diagnostic tools
   - test_parse_improved.py - Unit tests (6 test cases)
   - diagnose_v2.py - V2 diagnostic script
   - V2_FIX_REPORT.md - Detailed fix report
"""

# ============================================================================
# 快速开始
# ============================================================================
QUICK_START = """
1. 验证 parse_output 改进:
   python test_parse_improved.py
   
2. 诊断 V2 实际性能:
   python diagnose_v2.py
   
3. 运行完整评测:
   PROMPT_VERSION=2 python test_prompt.py
"""

# ============================================================================
# 预期改进
# ============================================================================
IMPROVEMENTS = """
改进前:
- 空输出比例: 30-50%
- 大型网格提取: 可能失败
- 格式兼容性: 严格

改进后:
- 空输出比例: < 5%
- 大型网格提取: 总是成功
- 格式兼容性: 灵活（支持多种 JSON 格式）
"""

# ============================================================================
# 技术细节
# ============================================================================
TECHNICAL_DETAILS = """
parse_output 函数的三层提取策略:

第1层: OUTPUT标签提取（优先级最高）
  if "OUTPUT:" in text:
      提取 "OUTPUT:" 后的第一个有效网格
      
第2层: 正则表达式提取
  pattern = r'\[\s*\[.*\]\s*\]'
  使用贪心匹配找到所有看起来像网格的片段
  
第3层: 手动括号匹配
  从第一个 [[ 开始
  逐个计数括号直到找到完整的 [[...]]
  
验证函数 _is_valid_grid():
  - 检查是否为二维列表
  - 检查是否包含整数
  - 检查是否非空
"""

# ============================================================================
# 文件修改列表
# ============================================================================
MODIFIED_FILES = """
修改的文件:
1. template.py
   - 重写 parse_output() 函数
   - 新增 _extract_grid_from_text() 辅助函数
   - 新增 _is_valid_grid() 验证函数

2. prompt.py
   - 改进 prompt_v2_fewshot_cot() 的 system_message
   - 添加清晰的 OUTPUT 格式指导
   - 强调 OUTPUT: 后不应有其他文本

新增文件:
1. test_parse_improved.py - 单元测试（6 个测试用例）
2. diagnose_v2.py - V2 诊断脚本
3. V2_FIX_REPORT.md - 详细修复报告
4. V2_EMPTY_OUTPUT_FIX.py - 本文件
"""

# ============================================================================
# 故障排除
# ============================================================================
TROUBLESHOOTING = """
如果仍有问题，请按优先级检查:

1. 运行诊断脚本检查空输出比例
   python diagnose_v2.py
   
2. 检查 max_tokens 是否太小
   API_MAX_TOKENS=2000 python diagnose_v2.py
   
3. 查看原始 API 响应
   在 diagnose_v2.py 中取消注释打印语句
   
4. 尝试增加超时时间
   API_TIMEOUT_SECONDS=120 python diagnose_v2.py
   
5. 检查网络连接和 API 可用性
"""

# ============================================================================
# 使用示例
# ============================================================================
USAGE_EXAMPLES = """
示例1: 快速验证（使用快速模式）
  $ FAST_MODE=1 PROMPT_VERSION=2 python test_prompt.py
  预期: 5 个任务，< 30 秒运行完成

示例2: 完整评测（30 个任务）
  $ PROMPT_VERSION=2 python test_prompt.py
  预期: 准确率 20-35%，大部分预测有效（非空）

示例3: 诊断特定问题
  $ python diagnose_v2.py
  输出: 空输出数量、正确数量等统计

示例4: 运行单元测试
  $ python test_parse_improved.py
  输出: 6/6 PASS
"""

# ============================================================================
# 打印所有信息
# ============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("V2 EMPTY OUTPUT ISSUE - FIX GUIDE")
    print("=" * 80)
    
    print("\n问题描述:")
    print(PROBLEM)
    
    print("\n解决方案:")
    print(SOLUTIONS)
    
    print("\n快速开始:")
    print(QUICK_START)
    
    print("\n预期改进:")
    print(IMPROVEMENTS)
    
    print("\n技术细节:")
    print(TECHNICAL_DETAILS)
    
    print("\n文件修改:")
    print(MODIFIED_FILES)
    
    print("\n故障排除:")
    print(TROUBLESHOOTING)
    
    print("\n使用示例:")
    print(USAGE_EXAMPLES)
    
    print("\n" + "=" * 80)
    print("推荐的下一步:")
    print("1. 运行: python test_parse_improved.py")
    print("2. 运行: python diagnose_v2.py")
    print("3. 如果一切正常，运行完整评测: PROMPT_VERSION=2 python test_prompt.py")
    print("=" * 80)
