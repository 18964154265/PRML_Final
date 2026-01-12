"""
prompt.py - 提示词构造策略
"""

import json


def prompt_v1_simple(d):
    """
    V1: 简单提示词（基础版本）
    直接给出训练样本和测试输入，要求模型预测
    """
    system_message = "You are an expert at solving visual reasoning tasks. Given input and output grid examples, identify the transformation rule and apply it to predict the output for new inputs."
    
    user_content = ""
    user_content += "Here are training examples:\n\n"
    for i, example in enumerate(d['train']):
        user_content += f"Example {i+1}:\n"
        user_content += f"Input:\n{json.dumps(example['input'])}\n"
        user_content += f"Output:\n{json.dumps(example['output'])}\n\n"
    
    user_content += "Now predict the output for this test input:\n"
    user_content += f"Input:\n{json.dumps(d['test'][0]['input'])}\n"
    user_content += "Output (as a 2D list):\n"
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_content}
    ]
    return messages


def prompt_v2_fewshot_cot(d):
    """
    V2: 基准推理流（Few-Shot + Chain of Thought）
    组合策略：少样本学习 + 链式思考
    
    流程：
    1. 少样本提示：使用 train 数据作为示例
    2. 链式思考：要求模型先生成自然语言的观察和规律总结
    3. 最终输出：然后生成预测的输出矩阵
    """
    system_message = """You are an expert at visual reasoning and pattern analysis. 
Your task is to:
1. Analyze the training examples carefully
2. Identify the transformation rule by comparing inputs and outputs
3. Write down your observations and reasoning in natural language
4. Then apply the rule to predict the test output

IMPORTANT: Your OUTPUT must be ONLY a valid 2D list of integers, nothing else after the final ]]
Example format: [[0,1,2],[3,4,5],[6,7,8]]"""
    
    user_content = ""
    user_content += "Analyze these training examples to identify the transformation pattern:\n\n"
    
    # 详细展示每个训练样本
    for i, example in enumerate(d['train']):
        user_content += f"Training Example {i+1}:\n"
        user_content += f"Input (shape {len(example['input'])}x{len(example['input'][0]) if example['input'] else 0}):\n"
        user_content += json.dumps(example['input']) + "\n"
        user_content += f"Output (shape {len(example['output'])}x{len(example['output'][0]) if example['output'] else 0}):\n"
        user_content += json.dumps(example['output']) + "\n\n"
    
    # 提供测试样本
    test_input = d['test'][0]['input']
    user_content += f"Test Input (shape {len(test_input)}x{len(test_input[0]) if test_input else 0}):\n"
    user_content += json.dumps(test_input) + "\n\n"
    
    user_content += """TASK: Analyze step by step and provide your final answer.

Step 1: OBSERVATIONS
What patterns do you notice? How does each input transform to output?

Step 2: PATTERN RULE
State the exact transformation rule clearly and concisely.

Step 3: REASONING
How does this rule apply to the test input? Show your work.

Step 4: OUTPUT (REQUIRED - Last line must be the 2D list only)
Compute the predicted output grid.
Your final output MUST be exactly in this format (no other text after this):
OUTPUT: [[...],[...],...]

CRITICAL: After "OUTPUT:", immediately provide ONLY the 2D list of integers with no additional text."""
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_content}
    ]
    return messages


def prompt_v3_robust(d):
    """
    V3: 鲁棒性增强流（Few-Shot + CoT + Self-Consistency）
    
    组合策略：少样本学习 + 链式思考 + 自我一致性
    
    核心思想：
    - 对同一个任务多次调用模型（使用不同的温度/采样参数）
    - 模型会生成不同的推理路径
    - 通过投票机制选择最常见的输出
    - 消除模型的"幻觉"和偶然错误
    
    此函数与 V2 的提示词相同，主要区别在于调用策略
    """
    system_message = """You are an expert at visual reasoning and pattern analysis. 
Your task is to:
1. Analyze the training examples carefully
2. Identify the transformation rule by comparing inputs and outputs
3. Write down your observations and reasoning in natural language
4. Then apply the rule to predict the test output

Format your response as:
OBSERVATIONS: [Describe what you see in the training examples]
PATTERN RULE: [State the transformation rule clearly]
REASONING: [Explain how this rule applies to the test case]
OUTPUT: [Provide the predicted grid as a 2D list]"""
    
    user_content = ""
    user_content += "Analyze these training examples to identify the transformation pattern:\n\n"
    
    # 详细展示每个训练样本
    for i, example in enumerate(d['train']):
        user_content += f"Training Example {i+1}:\n"
        user_content += f"Input (shape {len(example['input'])}x{len(example['input'][0]) if example['input'] else 0}):\n"
        user_content += json.dumps(example['input']) + "\n"
        user_content += f"Output (shape {len(example['output'])}x{len(example['output'][0]) if example['output'] else 0}):\n"
        user_content += json.dumps(example['output']) + "\n\n"
    
    # 提供测试样本
    test_input = d['test'][0]['input']
    user_content += f"Test Input (shape {len(test_input)}x{len(test_input[0]) if test_input else 0}):\n"
    user_content += json.dumps(test_input) + "\n\n"
    
    user_content += """Please analyze step by step:

1. OBSERVATIONS: What patterns do you notice? How does each input transform to output?

2. PATTERN RULE: State the exact transformation rule.

3. REASONING: How does this rule apply to the test input?

4. OUTPUT: Provide the predicted output as a 2D list of integers.

Format your final answer as:
OBSERVATIONS: [your observations]
PATTERN RULE: [the rule]
REASONING: [your reasoning]
OUTPUT: [the 2D list]"""
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_content}
    ]
    return messages


def prompt_v4_pal(d):
    """
    V4: 程序辅助语言模型 (Program-Aided Language Models - PAL)
    
    组合策略：少样本学习 + 代码生成
    
    核心思想：
    - 不要求模型直接输出数字矩阵
    - 要求模型编写一个 Python 函数来实现变换
    - 然后执行代码获得结果
    - 代码逻辑比直接猜测更严谨
    """
    system_message = """You are an expert programmer specializing in grid transformations and pattern analysis.
Your task is to:
1. Analyze the training examples to understand the transformation pattern
2. Write a Python function that implements this transformation
3. The function should work for any input grid following the same pattern

You will write a function named `transform(input_grid)` that:
- Takes a 2D list as input
- Returns a 2D list as output
- Implements the transformation rule observed from the training examples

Important:
- Only output valid Python code
- The code should be wrapped in a code block: ```python ... ```
- Make sure the function handles the transformation correctly
- Test your logic against the provided examples"""
    
    user_content = ""
    user_content += """Analyze these training examples and write a transformation function:

"""
    
    # 详细展示每个训练样本
    for i, example in enumerate(d['train']):
        user_content += f"Training Example {i+1}:\n"
        user_content += f"Input:\n{json.dumps(example['input'])}\n"
        user_content += f"Expected Output:\n{json.dumps(example['output'])}\n\n"
    
    # 提供测试样本
    test_input = d['test'][0]['input']
    user_content += f"""Based on the patterns above, write a Python function to transform the input:

Test Input:
{json.dumps(test_input)}

Instructions:
1. First, analyze what transformation is happening in the examples
2. Write a Python function named `transform(input_grid)` that implements this transformation
3. The function should return a 2D list (output grid)
4. Make sure the function works for all the training examples

Output your code in a Python code block:
```python
def transform(input_grid):
    # Your implementation here
    pass
```
"""
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_content}
    ]
    return messages


def prompt_v5_chain1_hypothesis(d):
    """
    V5 Chain 1 - 假设阶段
    让模型根据训练数据猜测一个变换规律
    """
    system_message = """You are an expert at analyzing patterns and transformation rules in visual puzzles.
Your task is to examine the training examples and propose a clear hypothesis about the transformation rule.
Focus on being precise and testable."""
    
    user_content = ""
    user_content += """Analyze these training examples and propose a transformation rule:

"""
    
    # 展示训练样本
    for i, example in enumerate(d['train']):
        user_content += f"Training Example {i+1}:\n"
        user_content += f"Input:\n{json.dumps(example['input'])}\n"
        user_content += f"Output:\n{json.dumps(example['output'])}\n\n"
    
    user_content += """Based on these examples, propose your hypothesis:

1. OBSERVATIONS: What patterns do you notice?
2. HYPOTHESIS: State your hypothesis about the transformation rule clearly and precisely.

Format your answer as:
OBSERVATIONS: [your observations]
HYPOTHESIS: [the transformation rule hypothesis]"""
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_content}
    ]
    return messages


def prompt_v5_reflexion_verify(d, hypothesis):
    """
    V5 Reflexion - 验证阶段
    让模型用提出的假设验证训练数据
    """
    system_message = """You are an expert at validating hypotheses about transformation rules.
Your task is to:
1. Apply the given hypothesis to each training input
2. Check if the result matches the expected training output
3. If there's a mismatch, identify the error and suggest a correction"""
    
    user_content = ""
    user_content += f"""Given this hypothesis:
{hypothesis}

Verify it against the training examples:

"""
    
    # 展示训练样本用于验证
    for i, example in enumerate(d['train']):
        user_content += f"Training Example {i+1}:\n"
        user_content += f"Input:\n{json.dumps(example['input'])}\n"
        user_content += f"Expected Output:\n{json.dumps(example['output'])}\n\n"
    
    user_content += """Now verify the hypothesis:

For each example:
1. Apply the hypothesis to the input
2. Compare with the expected output
3. If they match, say "✓ Correct"
4. If they don't match, say "✗ Mismatch" and explain what's wrong

After checking all examples:
- If all match, respond: "VERIFICATION: PASSED"
- If any don't match, respond with the corrections needed:
  "VERIFICATION: FAILED - ERROR ANALYSIS: [explain what's wrong] - CORRECTED HYPOTHESIS: [new hypothesis]"
"""
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_content}
    ]
    return messages


def prompt_v5_chain2_predict(d, final_hypothesis):
    """
    V5 Chain 2 - 应用阶段
    使用验证过的假设来预测测试输出
    """
    system_message = """You are an expert at applying validated transformation rules to new inputs.
Apply the given rule precisely to generate the output."""
    
    user_content = ""
    user_content += f"""Using this validated transformation rule:
{final_hypothesis}

Apply it to the test input:

"""
    
    test_input = d['test'][0]['input']
    user_content += f"Test Input:\n{json.dumps(test_input)}\n\n"
    
    user_content += """Generate the output:

Apply the rule step by step and provide:
OUTPUT: [the predicted output as a 2D list]
"""
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_content}
    ]
    return messages


def get_prompt_function(version=1):
    """
    获取指定版本的提示词函数
    
    参数:
    version (int): 提示词版本 (1-4)
    
    返回:
    function: 相应的提示词构造函数
    """
    prompt_functions = {
        1: prompt_v1_simple,
        2: prompt_v2_fewshot_cot,
        3: prompt_v3_robust,
        4: prompt_v4_pal
    }
    
    return prompt_functions.get(version, prompt_v1_simple)


def construct_prompt(d, version=1):
    """
    通用提示词构造函数
    
    参数:
    d (dict): ARC 任务数据
    version (int): 使用哪个版本的提示词 (1-4)
    
    返回:
    list: OpenAI API 格式的 messages
    """
    prompt_func = get_prompt_function(version)
    return prompt_func(d)

