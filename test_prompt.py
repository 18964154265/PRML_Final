# 这个文件的作用：在 ARC 的 jsonl 验证集上，串起完整的评测流程：
# 1）读取 jsonl 数据
# 2）对每个任务调用 construct_prompt 得到 prompt
# 3）调用大模型
# 4）用 parse_output 解析模型输出
# 5）统计有多少完全匹配 ground truth 并计算 accuracy

import os, json
from dotenv import load_dotenv
from openai import OpenAI
from template import construct_prompt, parse_output

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

    返回值：
        reply_text: 字符串（str），表示模型的主回答文本内容。
                    之后会被交给 parse_output(reply_text) 进行网格解析。
    """    # 从环境变量读取 API 配置
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    # 初始化 OpenAI 客户端（DeepSeek 兼容 OpenAI 接口）
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    # 调用 API
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature
    )
    
    # 提取回答文本
    reply_text = response.choices[0].message.content
    return reply_text

def main():
    """
    功能：
        串联整个评测流程，形成完整的 pipeline。
        主要步骤示意（具体实现由你在填代码时决定）：
    """

if __name__ == "__main__":
    main()

# 上面的函数只是作为示例框架，你可以任意修改和实现其中的逻辑