import json
import re


def extract_hypothesis(text):
    """
    从模型输出中提取假设/规律
    
    参数:
    text (str): 模型的回答文本
    
    返回:
    str: 提取的假设，如果没有找到则返回原文本
    """
    if not text:
        return ""
    
    # 尝试提取 HYPOTHESIS: ... 之后的内容
    pattern = r'HYPOTHESIS:\s*(.*?)(?=\n\n|$)'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    # 如果没有找到 HYPOTHESIS 标签，返回整个文本
    return text.strip()


def extract_corrected_hypothesis(text):
    """
    从验证反馈中提取修正后的假设
    
    参数:
    text (str): 模型的验证反馈
    
    返回:
    str: 修正后的假设，如果验证通过或无法提取则返回原假设
    """
    if not text:
        return ""
    
    # 检查是否验证通过
    if "VERIFICATION: PASSED" in text:
        return None  # 返回 None 表示验证通过
    
    # 尝试提取修正后的假设
    pattern = r'CORRECTED HYPOTHESIS:\s*(.*?)(?=\n\n|$)'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    # 尝试提取错误分析
    pattern = r'ERROR ANALYSIS:\s*(.*?)(?=\n\n|$)'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        error_info = match.group(1).strip()
        # 返回原文本中的所有信息用于调试
        return error_info
    
    return ""


def extract_python_code(text):
    """
    从模型输出中提取 Python 代码块
    
    参数:
    text (str): 模型的回答文本
    
    返回:
    str: 提取的 Python 代码，如果没有找到则返回空字符串
    """
    if not text:
        return ""
    
    # 匹配 ```python ... ``` 的代码块
    pattern = r'```python\s*(.*?)\s*```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        return matches[0]
    
    # 如果没有找到 ```python，尝试找任何 ``` 代码块
    pattern = r'```\s*(.*?)\s*```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        return matches[0]
    
    return ""


def execute_transform_code(code, test_input):
    """
    执行从模型生成的变换代码
    
    参数:
    code (str): 包含 transform 函数的 Python 代码
    test_input: 测试输入网格
    
    返回:
    list: 执行结果（输出网格），如果执行失败返回空列表
    """
    if not code:
        return []
    
    try:
        # 创建一个安全的执行环境
        exec_globals = {
            "json": json,
            "list": list,
            "dict": dict,
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "sum": sum,
            "min": min,
            "max": max,
            "set": set,
            "tuple": tuple,
            "sorted": sorted,
        }
        
        # 执行代码
        exec(code, exec_globals)
        
        # 检查 transform 函数是否存在
        if 'transform' not in exec_globals:
            return []
        
        # 调用 transform 函数
        transform_func = exec_globals['transform']
        result = transform_func(test_input)
        
        # 验证结果是否为有效的网格
        if not isinstance(result, list):
            return []
        
        # 检查是否为二维列表
        if len(result) == 0:
            return []
        
        for row in result:
            if not isinstance(row, list):
                return []
            for elem in row:
                if not isinstance(elem, int):
                    return []
        
        return result
    
    except Exception as e:
        print(f"    Code execution error: {str(e)}")
        return []


def parse_output(text):
    """
    解析大语言模型的输出文本，提取预测的网格
    
    参数:
    text (str): 大语言模型在设计prompt下的输出文本
    
    返回:
    list: 从输出文本解析出的二维数组 (Python列表，元素为整数)
    示例: [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
    
    """
    # 错误处理：空输入
    if not text or not isinstance(text, str):
        return []
    
    text = text.strip()
    if not text:
        return []
    
    try:
        # 策略 1: 首先尝试从 "OUTPUT:" 标签后面提取（优先级最高）
        if "OUTPUT:" in text:
            output_idx = text.find("OUTPUT:")
            substring = text[output_idx + len("OUTPUT:"):].strip()
            result = _extract_grid_from_text(substring)
            if result:
                return result
        
        # 策略 2: 尝试从整个文本中提取第一个有效的网格
        result = _extract_grid_from_text(text)
        if result:
            return result
        
        # 如果没有找到有效的数组，返回空列表
        return []
    
    except Exception as e:
        # 捕获其他异常
        return []


def _extract_grid_from_text(text):
    """
    从文本中提取第一个有效的网格
    使用多种策略提高鲁棒性
    """
    # 策略 A: 使用改进的正则表达式
    pattern = r'\[\s*\[.*?\]\s*\]'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for match in matches:
        try:
            result = json.loads(match)
            if _is_valid_grid(result):
                return result
        except (json.JSONDecodeError, ValueError):
            continue
    
    # 策略 B: 手动解析 - 查找第一个 [[ 并逐个匹配括号
    start_idx = text.find('[[')
    if start_idx != -1:
        bracket_count = 0
        result_str = ""
        
        for i in range(start_idx, len(text)):
            char = text[i]
            result_str += char
            
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                
                # 当括号数回到 0 时，我们找到了完整的数组
                if bracket_count == 0:
                    try:
                        result = json.loads(result_str)
                        if _is_valid_grid(result):
                            return result
                    except (json.JSONDecodeError, ValueError):
                        pass
                    break
    
    return None


def _is_valid_grid(obj):
    """
    检查对象是否为有效的网格（二维整数列表）
    """
    if not isinstance(obj, list):
        return False
    
    if len(obj) == 0:
        return False
    
    # 检查是否为二维列表且所有元素都是整数
    for row in obj:
        if not isinstance(row, list):
            return False
        if len(row) == 0:
            return False
        for elem in row:
            if not isinstance(elem, int):
                return False
    
    return True


def format_grid_for_markdown(grid, expected_grid=None):
    """
    将网格格式化为 markdown 表格中可用的格式
    
    参数:
    grid: 预测或期望的网格 (二维列表)
    expected_grid: 期望的网格（用于对比标记差异）
    
    返回:
    str: 格式化的网格字符串
    """
    if not grid:
        return "Error: Empty prediction"
    
    lines = []
    for i, row in enumerate(grid):
        row_str = "| "
        for j, elem in enumerate(row):
            if expected_grid and i < len(expected_grid) and j < len(expected_grid[i]):
                if elem != expected_grid[i][j]:
                    # 差异位置标记为粗斜体
                    row_str += f"***{elem}*** | "
                else:
                    row_str += f"{elem} | "
            else:
                row_str += f"{elem} | "
        lines.append(row_str)
    
    return "\n".join(lines)


def generate_markdown_report(tasks, predictions, ground_truths, prompt_version=1):
    """
    生成完整的 markdown 对比报告
    
    参数:
    tasks: 任务列表
    predictions: 预测结果列表
    ground_truths: 真值列表
    prompt_version: 使用的提示词版本
    
    返回:
    str: markdown 格式的完整报告
    """
    # 版本描述
    version_names = {
        1: "V1 - Simple",
        2: "V2 - Few-Shot + CoT",
        3: "V3 - Few-Shot + CoT + Self-Consistency",
        4: "V4 - Program-Aided Language Models (PAL)",
        5: "V5 - Prompt Chaining + Reflexion"
    }
    version_name = version_names.get(prompt_version, f"V{prompt_version}")
    
    markdown_content = f"# ARC Task Results - {version_name}\n\n"
    markdown_content += f"**Prompt Version:** {version_name}\n\n"
    markdown_content += f"Total Tasks: {len(tasks)}\n"
    markdown_content += f"Correct: {sum(p == g for p, g in zip(predictions, ground_truths))}\n"
    markdown_content += f"Accuracy: {sum(p == g for p, g in zip(predictions, ground_truths)) / len(tasks) if tasks else 0:.2%}\n\n"
    markdown_content += "---\n\n"
    
    for idx, (task, pred, ground_truth) in enumerate(zip(tasks, predictions, ground_truths)):
        is_correct = pred == ground_truth
        status = "✓ CORRECT" if is_correct else "✗ INCORRECT"
        
        markdown_content += f"## Task {idx + 1} {status}\n\n"
        markdown_content += "### Expected Output\n\n"
        markdown_content += format_grid_for_markdown(ground_truth) + "\n\n"
        
        markdown_content += "### Predicted Output\n\n"
        markdown_content += format_grid_for_markdown(pred, ground_truth) + "\n\n"
        
        markdown_content += "---\n\n"
    
    return markdown_content


def generate_input_visualization(tasks):
    """
    生成所有少样本示例的可视化报告
    
    参数:
    tasks: 任务列表
    
    返回:
    str: markdown 格式的可视化报告
    """
    markdown_content = "# ARC Training Examples Visualization\n\n"
    markdown_content += f"Total Tasks: {len(tasks)}\n\n"
    markdown_content += "---\n\n"
    
    for task_idx, task in enumerate(tasks):
        markdown_content += f"## Task {task_idx + 1}\n\n"
        
        train_examples = task.get('train', [])
        markdown_content += f"**Number of Training Examples: {len(train_examples)}**\n\n"
        
        for ex_idx, example in enumerate(train_examples):
            markdown_content += f"### Example {ex_idx + 1}\n\n"
            
            markdown_content += "#### Input\n\n"
            markdown_content += format_grid_for_markdown(example['input']) + "\n\n"
            
            markdown_content += "#### Output\n\n"
            markdown_content += format_grid_for_markdown(example['output']) + "\n\n"
        
        # 也显示测试输入
        test_examples = task.get('test', [])
        if test_examples:
            markdown_content += f"### Test Input (No Output)\n\n"
            markdown_content += format_grid_for_markdown(test_examples[0]['input']) + "\n\n"
        
        markdown_content += "---\n\n"
    
    return markdown_content


def voting_grids(grid_list):
    """
    自我一致性投票：从多个预测网格中选择最常见的一个
    
    参数:
    grid_list: 列表，包含多个预测网格 (每个都是二维列表)
    
    返回:
    list: 出现频率最高的网格，如果 grid_list 为空则返回空列表
    """
    if not grid_list:
        return []
    
    # 过滤掉空列表
    valid_grids = [g for g in grid_list if g]
    
    if not valid_grids:
        return []
    
    # 将每个网格转换为可哈希的格式（用于计数）
    grid_counts = {}
    for grid in valid_grids:
        # 转换为 tuple of tuples 以便作为字典键
        grid_key = tuple(tuple(row) for row in grid)
        grid_counts[grid_key] = grid_counts.get(grid_key, 0) + 1
    
    # 找出出现频率最高的网格
    most_common_key = max(grid_counts, key=grid_counts.get)
    most_common_grid = [list(row) for row in most_common_key]
    
    return most_common_grid


def get_voting_stats(grid_list):
    """
    获取投票统计信息
    
    参数:
    grid_list: 列表，包含多个预测网格
    
    返回:
    dict: 包含投票统计信息
        - "total_predictions": 总预测数
        - "valid_predictions": 有效预测数
        - "winning_grid": 投票赢家
        - "winning_count": 赢家出现次数
        - "confidence": 信心指数 (0-1)
    """
    if not grid_list:
        return {
            "total_predictions": 0,
            "valid_predictions": 0,
            "winning_grid": [],
            "winning_count": 0,
            "confidence": 0.0
        }
    
    valid_grids = [g for g in grid_list if g]
    
    if not valid_grids:
        return {
            "total_predictions": len(grid_list),
            "valid_predictions": 0,
            "winning_grid": [],
            "winning_count": 0,
            "confidence": 0.0
        }
    
    # 计数
    grid_counts = {}
    for grid in valid_grids:
        grid_key = tuple(tuple(row) for row in grid)
        grid_counts[grid_key] = grid_counts.get(grid_key, 0) + 1
    
    # 找出赢家
    most_common_key = max(grid_counts, key=grid_counts.get)
    winning_count = grid_counts[most_common_key]
    winning_grid = [list(row) for row in most_common_key]
    
    # 计算信心指数
    confidence = winning_count / len(valid_grids)
    
    return {
        "total_predictions": len(grid_list),
        "valid_predictions": len(valid_grids),
        "winning_grid": winning_grid,
        "winning_count": winning_count,
        "confidence": confidence
    }