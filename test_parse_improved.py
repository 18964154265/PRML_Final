#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试改进的 parse_output 函数
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from template import parse_output

# 测试用例集合
test_cases = [
    ("简单网格", "OUTPUT: [[0, 1], [2, 3]]", [[0, 1], [2, 3]]),
    ("带推理的网格", """
OBSERVATIONS: Pattern observation
PATTERN RULE: Rule description  
OUTPUT: [[0, 1, 0], [1, 0, 1], [0, 1, 0]]""", [[0, 1, 0], [1, 0, 1], [0, 1, 0]]),
    ("大型网格", "OUTPUT: [[0,1,2,3,4],[5,6,7,8,9],[0,1,2,3,4],[5,6,7,8,9],[0,1,2,3,4]]", 
     [[0,1,2,3,4],[5,6,7,8,9],[0,1,2,3,4],[5,6,7,8,9],[0,1,2,3,4]]),
    ("多个网格（应返回最后一个有效的）", """
First try: [[1, 2], [3, 4]]
Better attempt: [[5, 6], [7, 8]]
FINAL OUTPUT: [[0, 1], [2, 3]]""", [[0, 1], [2, 3]]),
    ("空网格返回空列表", "No grid here", []),
    ("嵌套网格with spaces", "OUTPUT: [ [ 1 , 2 ] , [ 3 , 4 ] ]", [[1, 2], [3, 4]]),
]

print("=" * 70)
print("Testing improved parse_output function")
print("=" * 70)

passed = 0
failed = 0

for test_name, input_text, expected_output in test_cases:
    result = parse_output(input_text)
    is_pass = result == expected_output
    
    if is_pass:
        passed += 1
        status = "PASS"
    else:
        failed += 1
        status = "FAIL"
    
    print(f"\n[{status}] {test_name}")
    print(f"  Input: {input_text[:80]}...")
    print(f"  Expected: {expected_output}")
    print(f"  Got: {result}")

print("\n" + "=" * 70)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 70)
