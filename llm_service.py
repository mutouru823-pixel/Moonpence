"""
llm_service.py
封装与 LLM API 交互的函数。
"""
import os
from typing import Optional

import openai


SYSTEM_PROMPT = (
    "你是一位世界顶级的文学大师。你的任务是接收原始文本，并严格按照用户指定的【目标作家风格】对其进行重写。"
    "深度解析该作家的句式节奏、标志性意象与情感距离。绝不可改变原文本的核心事件与基本逻辑。"
    "巧妙替换感官描写，使文字具有强烈的氛围感。不要输出任何解释性废话，直接输出润色后的正文。"
)


def generate_style_transfer(api_key: Optional[str], text: str, target_style: str, temperature: float = 0.8) -> str:
    """
    使用 OpenAI 的 Chat API 将文本重写为目标作家风格。

    参数：
    - api_key: OpenAI API Key（若为 None 或空字符串将抛出 ValueError）
    - text: 待润色的原始文本
    - target_style: 目标作家或风格名称
    - temperature: 模型随机性（0.0 - 1.0）

    返回值：重写后的文本（字符串）
    """
    if not api_key:
        raise ValueError("未提供 API Key。请在环境变量或函数参数中设置。")

    if not text or not text.strip():
        raise ValueError("待处理文本为空。")

    if not target_style or not target_style.strip():
        raise ValueError("目标作家风格不能为空。")

    # 设置 API Key
    openai.api_key = api_key

    # 构造用户提示，指导模型严格按指定风格重写
    user_prompt = (
        f"请将下面的文本以目标作家风格进行重写。目标作家/风格：{target_style}\n\n"
        f"原文：\n{text}\n\n请直接输出润色后的正文，不要添加解释或额外说明。"
    )

    try:
        # 使用 ChatCompletion API（兼容 gpt-3.5-turbo 及更高版本）
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=float(temperature),
            max_tokens=1500,
        )

        # 提取生成内容
        choices = response.get("choices", [])
        if not choices:
            raise RuntimeError("模型未返回结果。")

        generated_text = choices[0]["message"]["content"].strip()
        return generated_text

    except openai.error.OpenAIError as oe:
        # 将 OpenAI 的异常封装为 RuntimeError，调用方可捕获并显示友好信息
        raise RuntimeError(f"LLM 请求失败：{oe}")
