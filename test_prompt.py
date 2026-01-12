# 这个文件的作用：在 ARC 的 jsonl 验证集上，串起完整的评测流程：
# 1）读取 jsonl 数据
# 2）对每个任务调用 construct_prompt 得到 prompt
# 3）调用大模型
# 4）用 parse_output 解析模型输出
# 5）统计有多少完全匹配 ground truth 并计算 accuracy

import os, json, time
from dotenv import load_dotenv
from openai import OpenAI
from httpx import Timeout
from prompt import construct_prompt, prompt_v5_chain1_hypothesis, prompt_v5_reflexion_verify, prompt_v5_chain2_predict
from template import parse_output, generate_markdown_report, voting_grids, get_voting_stats, extract_python_code, execute_transform_code, extract_hypothesis, extract_corrected_hypothesis

# 加载 .env 文件
load_dotenv()

def load_jsonl(path):
    """
    功能：
        从给定的 jsonl 文件中读取所有样本，并返回一个列表，每个元素是一个任务字典。
        每一行对应一个 ARC 任务（例如包含 "train" / "test" 等字段）。

    输入参数：
        path: 字符串形式的文件路径，例如 "val.jsonl"。

    返回值：
        data: 列表（list），其中每个元素是一个字典（dict），表示一个 ARC 任务。
              例如 data[i] = d_i，其中 d_i 可以直接传给 construct_prompt(d_i) 使用。
    """
    data = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():  # 跳过空行
                data.append(json.loads(line))
    return data


def check_accuracy(predictions, ground_truths):
    """
    功能：
        计算模型预测结果与 ground truth 之间的“完全匹配”准确率。
        完全匹配指：预测网格与真实网格在尺寸和每个元素上都完全相同。

    输入参数：
        predictions: 列表（list）
                     每个元素是模型预测的输出网格（通常是一个二维列表，如 [[0,1],[1,0],...]）。
        ground_truths: 列表（list）
                       每个元素是对应样本的真实输出网格（二维列表）。

    返回值：
        accuracy: 浮点数（float），表示完全匹配的比例
    """    
    if len(predictions) == 0:
        return 0.0
    
    correct_count = 0
    for pred, ground_truth in zip(predictions, ground_truths):
        if pred == ground_truth:
            correct_count += 1
    
    accuracy = correct_count / len(predictions)
    return accuracy

def speak_and_listen(messages, model_name, temperature=0.0):
    """
    功能：
        调用大语言模型 API，将 messages 作为对话输入，返回模型生成的文本回答。

        注意：
        - messages 通常是一个符合 OpenAI / 其他厂商接口格式的列表，
          由 construct_prompt(d) 生成，例如：
          [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
            ...
          ]
        - 本函数只负责“发送请求 + 接收模型回答”，不做解析。

    输入参数：
        messages: 列表（list），对话内容，由 construct_prompt(d) 返回。
        model_name: 字符串（str），要调用的模型名称，例如 "gpt-4o-mini"。
        temperature: 浮点数（float），采样温度，控制随机性，默认 0.0。
        timeout: 整数（int），API 调用超时时间（秒），默认 60 秒。

    返回值：
        reply_text: 字符串（str），表示模型的主回答文本内容。
                    之后会被交给 parse_output(reply_text) 进行网格解析。
    """    # 从环境变量读取 API 配置
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    timeout = int(os.getenv("API_TIMEOUT_SECONDS", "60"))
    max_tokens = int(os.getenv("API_MAX_TOKENS", "1000"))
    
    # 初始化 OpenAI 客户端（DeepSeek 兼容 OpenAI 接口）
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=Timeout(timeout))
    
    # 调用 API
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    # 提取回答文本
    reply_text = response.choices[0].message.content
    return reply_text


def speak_and_listen_multiple(messages, model_name, num_samples=5, temperature=None):
    """
    多次调用模型获取多个预测（用于自我一致性投票）
    
    参数:
    messages: 对话消息列表
    model_name: 模型名称
    num_samples: 采样次数
    temperature: 采样温度，默认为 1.0
    
    返回:
    list: 多个预测结果列表
    """
    results = []
    
    for i in range(num_samples):
        try:
            # 使用固定的温度 1.0
            if temperature is None:
                temp = 1.0
            else:
                temp = temperature
            
            reply_text = speak_and_listen(messages, model_name, temperature=temp)
            results.append(reply_text)
            
            print(f"    Sample {i+1}/{num_samples} completed")
        except Exception as e:
            print(f"    Sample {i+1}/{num_samples} failed: {str(e)}")
            continue
    
    return results

def main():
    """
    功能：
        串联整个评测流程，形成完整的 pipeline。
        主要步骤示意（具体实现由你在填代码时决定）：
    """
    # 配置参数
    data_path = "val.jsonl"  # 可改为 "val_hard.jsonl"
    model_name = os.getenv("MODEL_NAME", "nex-n1")
    temperature = 1.0
    prompt_version = int(os.getenv("PROMPT_VERSION", "1"))  # 提示词版本 1-5
    num_samples_v3 = int(os.getenv("NUM_SAMPLES_V3", "5"))  # V3 的采样次数
    fast_mode = os.getenv("FAST_MODE", "0") == "1"  # 快速模式（仅测试前5个任务）
    api_timeout = int(os.getenv("API_TIMEOUT_SECONDS", "60"))  # API 超时时间（秒）
    
    # 1) 加载数据
    print(f"Loading data from {data_path}...")
    data = load_jsonl(data_path)
    print(f"Loaded {len(data)} tasks")
    print(f"Using prompt version: {prompt_version}")
    print(f"API timeout: {api_timeout} seconds")
    if fast_mode:
        print(f"⚡ FAST MODE: Testing on first 5 tasks only")
        data = data[:5]
    if prompt_version == 3:
        print(f"V3 will use {num_samples_v3} samples per task (self-consistency voting)")
    elif prompt_version == 5:
        print(f"V5 will use Prompt Chaining + Reflexion (multi-turn verification)")
    print()
    
    # 2) 初始化存储预测和真值的列表
    predictions = []
    ground_truths = []
    voting_stats_list = []  # 用于存储 V3 的投票统计
    task_times = []  # 用于记录每个任务的耗时
    
    total_start_time = time.time()
    
    # 3) 遍历每个任务
    for idx, task in enumerate(data):
        task_start_time = time.time()
        print(f"[{idx + 1}/{len(data)}] Processing task...")
        
        try:
            # 构造 prompt（使用指定版本）
            messages = construct_prompt(task, version=prompt_version)
            
            # 调用大模型
            print(f"  Calling model...")
            
            if prompt_version == 3:
                # V3: 自我一致性投票
                print(f"  Using self-consistency voting with {num_samples_v3} samples...")
                reply_texts = speak_and_listen_multiple(messages, model_name, num_samples=num_samples_v3)
                
                # 解析所有回答
                predicted_grids = [parse_output(text) for text in reply_texts]
                
                # 投票选择最常见的输出
                predicted_grid = voting_grids(predicted_grids)
                voting_stats = get_voting_stats(predicted_grids)
                voting_stats_list.append(voting_stats)
                
                print(f"  Voting: {voting_stats['valid_predictions']} valid predictions")
                print(f"  Winner appeared {voting_stats['winning_count']} times")
                print(f"  Confidence: {voting_stats['confidence']:.2%}")
            elif prompt_version == 4:
                # V4: Program-Aided Language Models (PAL)
                print(f"  Using Program-Aided Language Models (PAL)...")
                reply_text = speak_and_listen(messages, model_name, temperature)
                
                # 从回答中提取 Python 代码
                code = extract_python_code(reply_text)
                if code:
                    print(f"  Code extracted, executing...")
                    # 执行代码获得结果
                    test_input = task['test'][0]['input']
                    predicted_grid = execute_transform_code(code, test_input)
                    if predicted_grid:
                        print(f"  Code execution successful")
                    else:
                        print(f"  Code execution failed, trying to parse output...")
                        predicted_grid = parse_output(reply_text)
                else:
                    print(f"  No code found, falling back to parse_output...")
                    predicted_grid = parse_output(reply_text)
            elif prompt_version == 5:
                # V5: Prompt Chaining + Reflexion
                print(f"  Using Prompt Chaining + Reflexion...")
                
                # Chain 1: 假设
                print(f"    Chain 1: Generating hypothesis...")
                chain1_messages = prompt_v5_chain1_hypothesis(task)
                chain1_reply = speak_and_listen(chain1_messages, model_name, temperature)
                hypothesis = extract_hypothesis(chain1_reply)
                print(f"    Hypothesis: {hypothesis[:100]}...")
                
                # Reflexion: 验证
                print(f"    Reflexion: Verifying hypothesis...")
                reflexion_messages = prompt_v5_reflexion_verify(task, hypothesis)
                reflexion_reply = speak_and_listen(reflexion_messages, model_name, temperature)
                
                # 检查验证结果并可能修正
                if "VERIFICATION: PASSED" in reflexion_reply:
                    print(f"    ✓ Hypothesis verified!")
                    final_hypothesis = hypothesis
                else:
                    print(f"    ✗ Hypothesis needs correction")
                    corrected = extract_corrected_hypothesis(reflexion_reply)
                    if corrected:
                        final_hypothesis = corrected
                        print(f"    Corrected hypothesis: {corrected[:100]}...")
                    else:
                        final_hypothesis = hypothesis
                
                # Chain 2: 应用修正后的假设
                print(f"    Chain 2: Applying final hypothesis...")
                chain2_messages = prompt_v5_chain2_predict(task, final_hypothesis)
                chain2_reply = speak_and_listen(chain2_messages, model_name, temperature)
                predicted_grid = parse_output(chain2_reply)
            else:
                # V1 和 V2: 单次调用
                reply_text = speak_and_listen(messages, model_name, temperature)
                predicted_grid = parse_output(reply_text)
            
            # 获取真值
            ground_truth_grid = task['test'][0]['output']
            
            # 存储预测和真值
            predictions.append(predicted_grid)
            ground_truths.append(ground_truth_grid)
            
            # 输出本任务结果
            if predicted_grid == ground_truth_grid:
                print(f"  ✓ Correct!")
            else:
                print(f"  ✗ Incorrect")
                print(f"    Predicted: {predicted_grid}")
                print(f"    Expected:  {ground_truth_grid}")
        
        except Exception as e:
            print(f"  Error: {str(e)}")
            predictions.append([])
            ground_truths.append(task['test'][0]['output'])
        
        # 记录任务耗时
        task_time = time.time() - task_start_time
        task_times.append(task_time)
        print(f"  Time: {task_time:.2f}s")
        print()
    
    total_time = time.time() - total_start_time
    
    # 4) 计算准确率
    accuracy = check_accuracy(predictions, ground_truths)
    
    # 5) 输出结果到控制台
    print("=" * 50)
    print(f"Final Results:")
    print(f"  Accuracy: {accuracy:.2%} ({sum(p == g for p, g in zip(predictions, ground_truths))}/{len(data)})")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Avg time per task: {sum(task_times)/len(task_times):.2f}s")
    print(f"  Min/Max time: {min(task_times):.2f}s / {max(task_times):.2f}s")
    print("=" * 50)
    
    # 6) 生成 markdown 报告并追加保存
    print("\nGenerating markdown report...")
    markdown_report = generate_markdown_report(data, predictions, ground_truths, prompt_version=prompt_version)
    
    output_file = "output.md"
    
    # 以追加模式写入（append mode）
    with open(output_file, 'a', encoding='utf-8') as f:
        # 在不是第一次写入时，添加分隔符
        if os.path.getsize(output_file) > 0:
            f.write("\n" + "=" * 80 + "\n\n")
        f.write(markdown_report)
    
    print(f"Report appended to {output_file}")

if __name__ == "__main__":
    main()

# 上面的函数只是作为示例框架，你可以任意修改和实现其中的逻辑