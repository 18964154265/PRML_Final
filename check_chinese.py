#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# 读取文件
with open('paper.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 使用正则表达式进行通用翻译
# 这是一个更激进的方法 - 将所有剩余的中文部分转换

translation_dict = {
    '论文': 'Paper',
    '附录': 'Appendix',
    '系统': 'System',
    '消息': 'Message',
    '用户': 'User',
    '示例': 'Example',
    '信息': 'Information',
    '提示': 'Prompt',
    '输入': 'Input',
    '输出': 'Output',
    '采样': 'Sampling',
    '次数': 'Times',
    '阈值': 'Threshold',
    '置信度': 'Confidence',
    '阶段': 'Stage',
    '应用': 'Application',
    '完成': 'Complete',
    '任务': 'Task',
    '演示': 'Demonstration',
    '结果': 'Result',
    '分析': 'Analysis',
    '实现': 'Implementation',
    '详细': 'Detailed',
    '代码': 'Code',
    '执行': 'Execution',
    '训练': 'Training',
    '策略': 'Strategy',
}

# 执行逐字翻译会太粗糙，需要更精确的方法
# 让我们找出所有仍然包含中文的完整行

lines = content.split('\n')
chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')

for i, line in enumerate(lines):
    if chinese_pattern.search(line):
        # 检查这一行
        matches = chinese_pattern.findall(line)
        if matches and len(line.strip()) > 0:
            # 打印这一行以供检查
            print(f"Line {i+1}: {line[:100]}")

print("\n\nFound Chinese characters - need more specific translations")
