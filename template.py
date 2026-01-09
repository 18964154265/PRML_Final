import json
import re

def construct_prompt(d):
    """
    构造用于大语言模型的提示词
    
    参数:
    d (dict): jsonl数据文件的一行，解析成字典后的变量。
              注意：传入的 'd' 已经过处理，其 'test' 字段列表
              只包含 'input'，不包含 'output' 答案。
    
    返回:
    list: OpenAI API的message格式列表，允许设计多轮对话式的prompt
    示例: [{"role": "system", "content": "系统提示内容"}, 
           {"role": "user", "content": "用户提示内容"}]
    """
    
    # 系统提示
    system_message = "You are an expert at solving visual reasoning tasks. Given input and output grid examples, identify the transformation rule and apply it to predict the output for new inputs."
    
    # 构造用户提示
    user_content = ""
    
    # 添加训练样本
    user_content += "Here are training examples:\n\n"
    for i, example in enumerate(d['train']):
        user_content += f"Example {i+1}:\n"
        user_content += f"Input:\n{json.dumps(example['input'])}\n"
        user_content += f"Output:\n{json.dumps(example['output'])}\n\n"
    
    # 添加测试输入
    user_content += "Now predict the output for this test input:\n"
    user_content += f"Input:\n{json.dumps(d['test'][0]['input'])}\n"
    user_content += "Output (as a 2D list):\n"
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_content}
    ]
    
    return messages

def parse_output(text):
    """
    解析大语言模型的输出文本，提取预测的网格
    
    参数:
    text (str): 大语言模型在设计prompt下的输出文本
    
    返回:
    list: 从输出文本解析出的二维数组 (Python列表，元素为整数)
    示例: [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
    
    """
    # 实现输出解析逻辑
    return []