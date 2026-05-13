"""
llm_service.py
封装与 LLM API 交互的函数，支持多作家风格迁移与精细参数控制。
"""
import os
from typing import Optional

import openai


WRITER_STYLES = {
    "江南": (
        "江南的文风华丽而细腻，擅长用繁复的比喻和排比营造画面感。"
        "句式长短交错，偏爱在描写中埋入命运的隐喻。"
        "情感浓烈而克制，常以少年的视角审视世界，字里行间弥漫着孤独与宿命感。"
        "标志性意象：雨夜、樱花、天台、刀剑、龙的骸骨。"
    ),
    "村上春树": (
        "村上春树的文风简洁而疏离，用平淡克制的语调叙述不可思议之事。"
        "善于将超现实元素无缝融入日常，制造出平行世界的恍惚感。"
        "叙述者通常是独处的个体，在爵士乐、威士忌和意大利面之间游走。"
        "标志性意象：井、猫、耳朵、唱片、1960年代的摇滚乐、游泳池。"
    ),
    "三毛": (
        "三毛的文风真挚而自由，像一封写给远方的长信，娓娓道来。"
        "语言朴实却不失诗意，充满异域风情与人间烟火。"
        "情感细腻温暖，从不煽情，却能在平淡处让人动容。"
        "标志性意象：撒哈拉的落日、旧物、橄榄树、远行的背包、黄昏的海岸。"
    ),
    "余秋雨": (
        "余秋雨的文风厚重典雅，兼具学者的深邃与文人的敏感。"
        "语言精炼而富有韵律，善于从一砖一瓦中窥见文明的兴衰。"
        "行文间常有历史的回响与文化的忧思，思辨性强但不失温度。"
        "标志性意象：废墟、古道、碑文、书卷、雨中的古寺。"
    ),
    "毛姆": (
        "毛姆的文风冷峻犀利，以手术刀般的精准剖析人性。"
        "叙述冷静克制，常用第一人称旁观者视角，保持恰到好处的情感距离。"
        "善于在平静的叙述中突然抛出直击人心的金句。"
        "标志性意象：伦敦的雾、南洋的烈日、画布、手术台。"
    ),
    "张爱玲": (
        "张爱玲的文风华丽苍凉，用精致的比喻织就一张世情的网。"
        "善用通感手法，将颜色、气味、触感糅合出独特的氛围。"
        "对人情世故洞察入微，笔触间透出冷眼旁观的透彻与悲悯。"
        "标志性意象：月亮、旗袍、旧钟、沉香屑、电车铃声。"
    ),
    "鲁迅": (
        "鲁迅的文风冷峻深沉，如匕首投枪般锋利。"
        "语言精练到极致，一字一句皆有分量，善用反讽与白描。"
        "情感炽热却包裹在冷静的外壳之下，对国民性的批判入木三分。"
        "标志性意象：铁屋子、路、野草、昏黄的灯、呐喊。"
    ),
    "海明威": (
        "海明威的文风简洁硬朗，奉行「冰山原则」，八分之一在水面，八分之七在水下。"
        "短句为主，极少形容词，用名词和动词撑起骨架。"
        "对话干脆利落，留白极多，让读者从沉默中体会深意。"
        "标志性意象：大海、斗牛、拳击台、酒、清晨的街道。"
    ),
}


SYSTEM_PROMPT_BASE = (
    "你是一位世界顶级的文学大师，精通多种文学风格的重写与润色。"
    "你的任务是接收原始文本，并严格按照用户指定的【目标作家风格】对其进行重写。"
    "绝不可改变原文本的核心事件与基本逻辑。"
    "不要输出任何解释性废话，直接输出润色后的正文。"
)


def _build_system_prompt(target_style: str) -> str:
    """根据目标风格构建定制化的系统提示。"""
    style_desc = WRITER_STYLES.get(target_style)
    if style_desc:
        return (
            f"{SYSTEM_PROMPT_BASE}\n\n"
            f"【目标作家风格指南】\n"
            f"目标作家：{target_style}\n"
            f"风格特征：{style_desc}\n\n"
            f"请严格遵循以上风格指南进行重写。深入模仿该作家的句式节奏、用词习惯、"
            f"情感距离和标志性意象。如果合适，可以在不改变原意的前提下融入该作家常用的意象元素。"
        )
    else:
        return (
            f"{SYSTEM_PROMPT_BASE}\n\n"
            f"目标风格：{target_style}\n"
            f"请根据你对这位作家/风格的理解，对文本进行符合该风格的重写。"
        )


def generate_style_transfer(
    api_key: Optional[str],
    text: str,
    target_style: str,
    temperature: float = 0.8,
    style_intensity: str = "适中",
    target_word_count: Optional[int] = None,
    output_mode: str = "纯文本",
    api_base: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
) -> str:
    """
    使用 OpenAI 的 Chat API 将文本重写为目标作家风格。

    参数：
    - api_key: OpenAI API Key
    - text: 待润色的原始文本
    - target_style: 目标作家或风格名称
    - temperature: 模型随机性 (0.0 - 1.0)
    - style_intensity: 风格化强度 ("轻度", "适中", "重度")
    - target_word_count: 目标字数（可选，None 表示不限制）
    - output_mode: 输出模式 ("纯文本", "逐段对照", "润色+解析")
    - api_base: API 地址（可选，用于代理或兼容接口）
    - model: 模型名称（默认 gpt-3.5-turbo）

    返回值：重写后的文本（字符串）
    """
    if not api_key:
        raise ValueError("未提供 API Key。请在环境变量或函数参数中设置。")

    if not text or not text.strip():
        raise ValueError("待处理文本为空。")

    if not target_style or not target_style.strip():
        raise ValueError("目标作家风格不能为空。")

    openai.api_key = api_key
    if api_base:
        openai.api_base = api_base

    system_prompt = _build_system_prompt(target_style)

    intensity_map = {
        "轻度": "轻度风格化：保留原文的大部分结构和用词，仅在关键处融入目标作家的语感和意象，使文字带有该作家的「气息」即可。",
        "适中": "适中风格化：在保留原意的基础上，全面改写句式节奏、用词习惯和意象选择，使文字明显呈现目标作家的风格特征。",
        "重度": "重度风格化：彻底按照目标作家的风格进行创作级重写，可以重组段落结构、大胆替换意象，甚至在合理范围内微调叙事视角，力求达到以假乱真的效果。",
    }
    intensity_instruction = intensity_map.get(style_intensity, intensity_map["适中"])

    word_count_instruction = ""
    if target_word_count and target_word_count > 0:
        word_count_instruction = f"输出字数控制在约 {target_word_count} 字左右。"

    output_mode_instruction = ""
    if output_mode == "逐段对照":
        output_mode_instruction = (
            "请按照以下格式输出：将原文分段，每一段先输出「【原文】」标记的原始段落，"
            "紧接着输出「【润色】」标记的对应润色段落，逐段交替排列。"
        )
    elif output_mode == "润色+解析":
        output_mode_instruction = (
            "请按照以下格式输出：先输出完整的润色后正文，然后另起一行用「---」分隔，"
            "下方简要列出 3-5 条润色要点（每条以「· 」开头），"
            "说明你在润色中运用了该作家的哪些风格特征。"
        )

    user_prompt_parts = [
        f"目标作家/风格：{target_style}",
        f"风格化强度：{intensity_instruction}",
    ]
    if word_count_instruction:
        user_prompt_parts.append(word_count_instruction)
    if output_mode_instruction:
        user_prompt_parts.append(output_mode_instruction)

    user_prompt_parts.append(f"原文：\n{text}")
    user_prompt_parts.append("请直接按要求输出，不要添加额外解释。")

    user_prompt = "\n\n".join(user_prompt_parts)

    max_tokens = target_word_count * 3 if target_word_count else 2000
    max_tokens = max(500, min(max_tokens, 4000))

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=float(temperature),
            max_tokens=max_tokens,
        )

        choices = response.get("choices", [])
        if not choices:
            raise RuntimeError("模型未返回结果。")

        generated_text = choices[0]["message"]["content"].strip()
        return generated_text

    except openai.error.OpenAIError as oe:
        raise RuntimeError(f"LLM 请求失败：{oe}")