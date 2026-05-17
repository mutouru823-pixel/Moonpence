"""
llm_service.py
封装与 LLM API 交互的函数，支持风格样本学习、精细参数控制、评分迭代和风格混合。
"""
from typing import Optional, Dict, Any
import json
import os
from pathlib import Path
from datetime import datetime
from uuid import uuid4


# 自定义风格存储路径
CUSTOM_STYLES_FILE = Path.home() / ".moonpence" / "custom_styles.json"
DIARY_LIBRARY_FILE = Path.home() / ".moonpence" / "diary_library.json"


def _ensure_custom_styles_dir():
    """确保自定义风格目录存在"""
    CUSTOM_STYLES_FILE.parent.mkdir(parents=True, exist_ok=True)


def _ensure_diary_library_dir():
    """确保日记库目录存在"""
    DIARY_LIBRARY_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_custom_styles() -> Dict[str, str]:
    """
    从本地文件加载自定义风格。
    返回字典：{风格名称: 风格描述}
    """
    _ensure_custom_styles_dir()
    if CUSTOM_STYLES_FILE.exists():
        try:
            with open(CUSTOM_STYLES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_custom_style(style_name: str, style_description: str) -> bool:
    """
    保存一个自定义风格。
    返回是否成功。
    """
    _ensure_custom_styles_dir()
    try:
        custom_styles = load_custom_styles()
        custom_styles[style_name] = style_description
        with open(CUSTOM_STYLES_FILE, 'w', encoding='utf-8') as f:
            json.dump(custom_styles, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def delete_custom_style(style_name: str) -> bool:
    """
    删除一个自定义风格。
    返回是否成功。
    """
    try:
        custom_styles = load_custom_styles()
        if style_name in custom_styles:
            del custom_styles[style_name]
            _ensure_custom_styles_dir()
            with open(CUSTOM_STYLES_FILE, 'w', encoding='utf-8') as f:
                json.dump(custom_styles, f, ensure_ascii=False, indent=2)
            return True
        return False
    except Exception:
        return False


def get_all_styles() -> Dict[str, str]:
    """
    获取所有风格（预设 + 自定义）。
    返回合并后的字典。
    """
    all_styles = WRITER_STYLES.copy()
    custom_styles = load_custom_styles()
    all_styles.update(custom_styles)
    return all_styles


def load_diary_library() -> list:
    """
    加载本地日记库。
    返回按创建时间倒序排列的条目列表。
    """
    _ensure_diary_library_dir()
    if DIARY_LIBRARY_FILE.exists():
        try:
            with open(DIARY_LIBRARY_FILE, 'r', encoding='utf-8') as f:
                entries = json.load(f)
                if isinstance(entries, list):
                    return sorted(entries, key=lambda item: item.get("created_at", ""), reverse=True)
        except Exception:
            return []
    return []


def save_diary_entry(
    title: str,
    content: str,
    notes: str = "",
    style_name: str = "",
    mode: str = "日记补全",
    previous_entry: str = "",
) -> str:
    """
    保存一篇日记到本地日记库。
    返回保存后的条目 ID。
    """
    _ensure_diary_library_dir()
    entry = {
        "id": uuid4().hex,
        "title": title.strip() or "未命名日记",
        "content": content.strip(),
        "notes": notes.strip(),
        "style_name": style_name.strip(),
        "mode": mode,
        "previous_entry": previous_entry.strip(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }

    entries = load_diary_library()
    entries.insert(0, entry)
    with open(DIARY_LIBRARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    return entry["id"]


def delete_diary_entry(entry_id: str) -> bool:
    """
    删除日记库中的某条记录。
    """
    try:
        entries = load_diary_library()
        filtered_entries = [entry for entry in entries if entry.get("id") != entry_id]
        if len(filtered_entries) == len(entries):
            return False
        _ensure_diary_library_dir()
        with open(DIARY_LIBRARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(filtered_entries, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_diary_entry(entry_id: str) -> Dict[str, Any]:
    """
    通过 ID 获取单条日记。
    """
    for entry in load_diary_library():
        if entry.get("id") == entry_id:
            return entry
    return {}


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


def _call_chat_api(
    api_key: str,
    api_base: Optional[str],
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """调用 OpenAI 兼容 Chat API，兼容旧版 (0.x) 和新版 (1.x) SDK。"""
    base_url = None
    if api_base:
        base = api_base.rstrip("/")
        if not base.endswith("/v1"):
            base = base + "/v1"
        base_url = base

    try:
        import openai as _openai

        if hasattr(_openai, "OpenAI"):
            client = _openai.OpenAI(api_key=api_key, base_url=base_url)
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content.strip()
        else:
            _openai.api_key = api_key
            if base_url:
                _openai.api_base = base_url
            resp = _openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=float(temperature),
                max_tokens=max_tokens,
            )
            choices = resp.get("choices", [])
            if not choices:
                raise RuntimeError("模型未返回结果。")
            return choices[0]["message"]["content"].strip()

    except Exception as e:
        raise RuntimeError(f"LLM 请求失败：{e}")


def analyze_style_samples(
    api_key: str,
    api_base: Optional[str],
    model: str,
    samples: str,
) -> str:
    """
    分析用户提供的风格样本，提取风格特征。
    """
    system_prompt = (
        "你是一位资深文学评论家，擅长分析作家的写作风格。"
        "你的任务是分析提供的文本样本，提取以下信息："
        "1. 句式特点（平均句长、节奏）"
        "2. 用词偏好（形容词/动词/名词比例、常用意象）"
        "3. 情感基调"
        "4. 叙事视角"
        "5. 标志性元素"
        "请用清晰的中文段落总结这些特征。"
    )
    user_prompt = f"请分析以下文本的写作风格特征：\n\n{samples}"
    return _call_chat_api(
        api_key=api_key,
        api_base=api_base,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=2000,
    )


def evaluate_result(
    api_key: str,
    api_base: Optional[str],
    model: str,
    original_text: str,
    rewritten_text: str,
    target_style: str,
    style_blend: Optional[Dict[str, float]] = None,
) -> str:
    """
    评估润色结果，给出评分和改进建议。
    """
    target_desc = f"目标风格：{target_style}"
    if style_blend:
        blend_desc = [f"{writer} ({weight * 100:.0f}%)" for writer, weight in style_blend.items()]
        target_desc = f"混合风格：{' + '.join(blend_desc)}"
    
    system_prompt = (
        "你是一位严格公正的文学评论家。请评估以下润色结果："
        "1. 给出 0-10 的风格相似度评分"
        "2. 指出哪些地方还不够像目标风格"
        "3. 给出具体的改进建议"
        "请用简洁的中文回答，格式清晰。"
    )
    
    user_prompt = (
        f"原文：\n{original_text}\n\n"
        f"润色结果：\n{rewritten_text}\n\n"
        f"{target_desc}\n\n"
        "请评估这个润色结果。"
    )
    
    return _call_chat_api(
        api_key=api_key,
        api_base=api_base,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=1500,
    )


def _build_system_prompt(
    target_style: str,
    style_samples: Optional[str] = None,
    style_analysis: Optional[str] = None,
    style_blend: Optional[Dict[str, float]] = None,
) -> str:
    """根据目标风格、风格混合参数构建定制化的系统提示。"""
    prompt = SYSTEM_PROMPT_BASE
    
    # 处理风格混合
    if style_blend:
        prompt += "\n\n【混合风格指南】"
        for writer, weight in style_blend.items():
            writer_desc = WRITER_STYLES.get(writer)
            if writer_desc:
                prompt += f"\n- {writer} ({weight * 100:.0f}%): {writer_desc}"
        prompt += f"\n\n请按照上述作家的混合风格进行重写，权重按各比例分配。"
    else:
        style_desc = WRITER_STYLES.get(target_style)
        if style_desc:
            prompt += f"\n\n【目标作家风格指南】\n目标作家：{target_style}\n风格特征：{style_desc}"
    
    if style_samples:
        prompt += f"\n\n【用户提供的风格样本】\n{style_samples}"
    
    if style_analysis:
        prompt += f"\n\n【风格样本分析结果】\n{style_analysis}"
    
    if style_samples or style_analysis or style_blend:
        prompt += (
            "\n\n请严格遵循以上风格指南进行重写。深入模仿该作家的句式节奏、用词习惯、"
            "情感距离和标志性意象。如果合适，可以在不改变原意的前提下融入该作家常用的意象元素。"
        )
    elif style_desc:
        prompt += (
            "\n\n请严格遵循以上风格指南进行重写。深入模仿该作家的句式节奏、用词习惯、"
            "情感距离和标志性意象。如果合适，可以在不改变原意的前提下融入该作家常用的意象元素。"
        )
    else:
        prompt += f"\n\n目标风格：{target_style}\n请根据你对这位作家/风格的理解，对文本进行符合该风格的重写。"
    
    return prompt


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
    style_samples: Optional[str] = None,
    style_analysis: Optional[str] = None,
    style_blend: Optional[Dict[str, float]] = None,
    evaluation_feedback: Optional[str] = None,
) -> str:
    """
    使用 OpenAI 兼容的 Chat API 将文本重写为目标作家风格。

    参数：
    - api_key: API Key
    - text: 待润色的原始文本
    - target_style: 目标作家或风格名称
    - temperature: 模型随机性 (0.0 - 1.0)
    - style_intensity: 风格化强度 ("轻度", "适中", "重度")
    - target_word_count: 目标字数（可选，None 表示不限制）
    - output_mode: 输出模式 ("纯文本", "逐段对照", "润色+解析")
    - api_base: API 地址（可选，用于 DeepSeek / 代理 / 兼容接口）
    - model: 模型名称（默认 gpt-3.5-turbo）
    - style_samples: 用户提供的风格样本（可选）
    - style_analysis: 风格样本分析结果（可选）
    - style_blend: 风格混合配置（可选，字典如 {"江南": 0.7, "村上春树": 0.3}）
    - evaluation_feedback: 评分反馈（可选，用于迭代优化）

    返回值：重写后的文本（字符串）
    """
    if not api_key:
        raise ValueError("未提供 API Key。请在环境变量或函数参数中设置。")

    if not text or not text.strip():
        raise ValueError("待处理文本为空。")

    if not target_style or not target_style.strip():
        if not style_blend:
            raise ValueError("目标作家风格或风格混合配置不能为空。")

    system_prompt = _build_system_prompt(
        target_style=target_style,
        style_samples=style_samples,
        style_analysis=style_analysis,
        style_blend=style_blend,
    )

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

    user_prompt_parts = []
    
    if style_blend:
        blend_desc = [f"{writer} ({weight * 100:.0f}%)" for writer, weight in style_blend.items()]
        user_prompt_parts.append(f"混合风格：{' + '.join(blend_desc)}")
    else:
        user_prompt_parts.append(f"目标作家/风格：{target_style}")
    
    user_prompt_parts.append(f"风格化强度：{intensity_instruction}")
    
    if word_count_instruction:
        user_prompt_parts.append(word_count_instruction)
    if output_mode_instruction:
        user_prompt_parts.append(output_mode_instruction)
    
    if evaluation_feedback:
        user_prompt_parts.append(f"上次润色的评价反馈：\n{evaluation_feedback}\n\n请根据这些反馈进一步优化润色结果。")

    user_prompt_parts.append(f"原文：\n{text}")
    user_prompt_parts.append("请直接按要求输出，不要添加额外解释。")

    user_prompt = "\n\n".join(user_prompt_parts)

    max_tokens = target_word_count * 3 if target_word_count else 2000
    max_tokens = max(500, min(max_tokens, 4000))

    return _call_chat_api(
        api_key=api_key,
        api_base=api_base,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=float(temperature),
        max_tokens=max_tokens,
    )


def complete_diary_entry(
    api_key: Optional[str],
    notes: str,
    target_style: str,
    temperature: float = 0.7,
    api_base: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
    style_samples: Optional[str] = None,
    style_analysis: Optional[str] = None,
    style_blend: Optional[Dict[str, float]] = None,
    date_hint: Optional[str] = None,
    scene_hint: Optional[str] = None,
) -> str:
    """
    根据简短记录，补全成具有目标文风的日记正文。

    参数：
    - api_key: API Key
    - notes: 用户记录的日记要点
    - target_style: 目标作家或风格名称
    - temperature: 模型随机性
    - api_base: API 地址
    - model: 模型名称
    - style_samples: 用户提供的风格样本（可选）
    - style_analysis: 风格样本分析结果（可选）
    - style_blend: 风格混合配置（可选）
    - date_hint: 日期提示（可选）
    - scene_hint: 场景提示（可选）

    返回值：补全后的日记正文（字符串）
    """
    if not api_key:
        raise ValueError("未提供 API Key。请在环境变量或函数参数中设置。")

    if not notes or not notes.strip():
        raise ValueError("日记要点不能为空。")

    if not target_style or not target_style.strip():
        if not style_blend:
            raise ValueError("目标作家风格或风格混合配置不能为空。")

    system_prompt = _build_system_prompt(
        target_style=target_style,
        style_samples=style_samples,
        style_analysis=style_analysis,
        style_blend=style_blend,
    )
    system_prompt += (
        "\n\n【日记补全任务】"
        "你将收到用户用简短笔记记录的日记要点，请将其补写成一篇完整、自然、连贯的日记。"
        "必须保留用户提供的事实、人物、时间、地点和事件，不要擅自新增关键事实或改变时间线。"
        "可以合理补充过渡句、细节描写和心理活动，让文本更像真实日记，但不要写成空泛抒情。"
        "优先使用第一人称，语气贴近日常记录。"
        "如果用户提供了日期或场景提示，请自然融入正文。"
        "直接输出补全后的日记正文，不要附加说明。"
    )

    user_prompt_parts = []
    if style_blend:
        blend_desc = [f"{writer} ({weight * 100:.0f}%)" for writer, weight in style_blend.items()]
        user_prompt_parts.append(f"混合风格：{' + '.join(blend_desc)}")
    else:
        user_prompt_parts.append(f"目标作家/风格：{target_style}")

    if date_hint:
        user_prompt_parts.append(f"日期提示：{date_hint}")
    if scene_hint:
        user_prompt_parts.append(f"场景提示：{scene_hint}")
    if style_samples:
        user_prompt_parts.append(f"风格样本：\n{style_samples}")
    if style_analysis:
        user_prompt_parts.append(f"风格分析：\n{style_analysis}")

    user_prompt_parts.append(
        "请将以下简短记录补写成完整日记，保留事实并尽量贴近目标文风：\n\n"
        f"{notes.strip()}"
    )
    user_prompt_parts.append("请直接输出完整日记正文。")

    user_prompt = "\n\n".join(user_prompt_parts)

    max_tokens = max(700, min(len(notes) * 4, 3500))

    return _call_chat_api(
        api_key=api_key,
        api_base=api_base,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=float(temperature),
        max_tokens=max_tokens,
    )


def continue_diary_entry(
    api_key: Optional[str],
    previous_entry: str,
    notes: str,
    target_style: str,
    temperature: float = 0.7,
    api_base: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
    style_samples: Optional[str] = None,
    style_analysis: Optional[str] = None,
    style_blend: Optional[Dict[str, float]] = None,
    date_hint: Optional[str] = None,
    scene_hint: Optional[str] = None,
) -> str:
    """
    根据前一天日记和当日要点，续写成连续多天日记。
    """
    if not api_key:
        raise ValueError("未提供 API Key。请在环境变量或函数参数中设置。")

    if not previous_entry or not previous_entry.strip():
        raise ValueError("前一天日记不能为空。")

    if not notes or not notes.strip():
        raise ValueError("当日日记要点不能为空。")

    if not target_style or not target_style.strip():
        if not style_blend:
            raise ValueError("目标作家风格或风格混合配置不能为空。")

    system_prompt = _build_system_prompt(
        target_style=target_style,
        style_samples=style_samples,
        style_analysis=style_analysis,
        style_blend=style_blend,
    )
    system_prompt += (
        "\n\n【连续多天日记任务】"
        "你将收到前一天的日记正文和今天的简短要点，请续写今天的日记。"
        "续写时要自然承接前一天的情绪、人物关系、未完成的事情和叙事口吻，形成连续感。"
        "不要重复前一天已经写过的内容，不要把今天写成独立无关的新文。"
        "必须保留用户提供的事实、人物、时间、地点和事件，不要擅自新增关键事实或改变时间线。"
        "优先使用第一人称，语气贴近日常记录。"
        "如果用户提供了日期或场景提示，请自然融入正文。"
        "直接输出今天这一篇续写后的完整日记正文，不要附加说明。"
    )

    user_prompt_parts = []
    if style_blend:
        blend_desc = [f"{writer} ({weight * 100:.0f}%)" for writer, weight in style_blend.items()]
        user_prompt_parts.append(f"混合风格：{' + '.join(blend_desc)}")
    else:
        user_prompt_parts.append(f"目标作家/风格：{target_style}")

    if date_hint:
        user_prompt_parts.append(f"日期提示：{date_hint}")
    if scene_hint:
        user_prompt_parts.append(f"场景提示：{scene_hint}")
    if style_samples:
        user_prompt_parts.append(f"风格样本：\n{style_samples}")
    if style_analysis:
        user_prompt_parts.append(f"风格分析：\n{style_analysis}")

    user_prompt_parts.append(f"前一天日记：\n{previous_entry.strip()}")
    user_prompt_parts.append(
        "今天的简短记录：\n"
        f"{notes.strip()}"
    )
    user_prompt_parts.append("请直接输出今天的完整日记正文。")

    user_prompt = "\n\n".join(user_prompt_parts)
    max_tokens = max(900, min((len(previous_entry) + len(notes)) * 3, 4000))

    return _call_chat_api(
        api_key=api_key,
        api_base=api_base,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=float(temperature),
        max_tokens=max_tokens,
    )


def refine_custom_style_description(
    api_key: Optional[str],
    api_base: Optional[str],
    model: str,
    style_name: str,
    current_description: str,
    new_samples: str,
) -> str:
    """
    基于现有自定义风格和新增样本，更新风格描述。
    """
    if not api_key:
        raise ValueError("未提供 API Key。请在环境变量或函数参数中设置。")

    if not style_name or not style_name.strip():
        raise ValueError("风格名称不能为空。")

    if not current_description or not current_description.strip():
        raise ValueError("现有风格描述不能为空。")

    if not new_samples or not new_samples.strip():
        raise ValueError("新增训练文本不能为空。")

    system_prompt = (
        "你是一位资深的文学风格训练师。你的任务是基于一个已存在的自定义风格，"
        "结合新增文本样本，输出一份更新后的风格描述。"
        "要求：1. 保留原有风格的核心特征；2. 吸收新增样本中稳定、重复出现的特征；"
        "3. 不要把偶发内容误当成核心风格；4. 输出中文、自然、可直接用于后续写作控制。"
        "请直接输出更新后的风格描述，不要加标题、编号或解释。"
    )
    user_prompt = (
        f"风格名称：{style_name}\n\n"
        f"现有风格描述：\n{current_description}\n\n"
        f"新增训练文本：\n{new_samples}\n\n"
        "请基于以上内容，生成更新后的风格描述。"
    )

    return _call_chat_api(
        api_key=api_key,
        api_base=api_base,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=1800,
    )


def compute_style_features(text: str) -> dict:
    """
    计算文本的风格特征，用于可视化对比。
    返回包含统计信息的字典。
    """
    import re
    
    # 句子统计
    sentences = re.split(r'[。！？；]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    total_chars = len(text)
    
    # 尝试使用 jieba
    total_words = total_chars  # 备用方案
    positive_count = 0
    negative_count = 0
    avg_sentence_length = total_chars / len(sentences) if sentences else 0
    
    try:
        import jieba
        words = list(jieba.cut(text))
        total_words = len(words)
        
        # 常见情绪词统计
        positive_words = ['好', '美', '爱', '快乐', '幸福', '成功', '希望', '光明']
        negative_words = ['坏', '丑', '恨', '悲伤', '痛苦', '失败', '绝望', '黑暗']
        positive_count = sum(1 for w in words if w in positive_words)
        negative_count = sum(1 for w in words if w in negative_words)
    except ImportError:
        pass
    
    return {
        "avg_sentence_length": avg_sentence_length,
        "total_sentences": len(sentences),
        "total_chars": total_chars,
        "total_words": total_words,
        "positive_count": positive_count,
        "negative_count": negative_count,
    }
