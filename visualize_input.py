"""
可视化脚本：将所有少样本示例（训练样本）输出到 input.md
"""

import json
from template import generate_input_visualization


def load_jsonl(path):
    """加载 JSONL 文件"""
    data = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def main():
    """主函数"""
    # 配置参数
    data_path = "val.jsonl"  # 可改为 "val_hard.jsonl"
    output_file = "input.md"
    
    # 1) 加载数据
    print(f"Loading data from {data_path}...")
    data = load_jsonl(data_path)
    print(f"Loaded {len(data)} tasks\n")
    
    # 2) 生成可视化报告
    print("Generating input visualization...")
    markdown_report = generate_input_visualization(data)
    
    # 3) 保存到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_report)
    
    print(f"Visualization saved to {output_file}")


if __name__ == "__main__":
    main()
