import os
import streamlit as st
from dotenv import load_dotenv

from llm_service import generate_style_transfer, WRITER_STYLES


load_dotenv()

PRESET_WRITERS = list(WRITER_STYLES.keys())


def _init_session():
    defaults = {
        "history": [],
        "api_key_configured": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_sidebar():
    st.sidebar.markdown("## 设置")

    env_api_key = os.environ.get("OPENAI_API_KEY", "")
    api_key_input = st.sidebar.text_input(
        "OpenAI API Key",
        value=env_api_key,
        type="password",
        placeholder="sk-...",
        help="若不设置环境变量，请在此填入 API Key",
    )

    env_api_base = os.environ.get("OPENAI_BASE_URL", "")
    api_base_input = st.sidebar.text_input(
        "API 地址",
        value=env_api_base,
        placeholder="https://api.openai.com/v1",
        help="默认为 OpenAI 官方地址，可填入代理或兼容接口地址",
    )

    env_model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    model_name_input = st.sidebar.text_input(
        "模型名称",
        value=env_model,
        placeholder="gpt-3.5-turbo",
        help="例如 gpt-4o、deepseek-chat、qwen-turbo 等",
    )

    st.sidebar.markdown("---")

    st.sidebar.markdown("### 创作参数")

    temperature = st.sidebar.slider(
        "创造性 (Temperature)",
        min_value=0.0,
        max_value=1.0,
        value=0.8,
        step=0.05,
        help="越高越有创造性，越低越稳定保守",
    )

    style_intensity = st.sidebar.select_slider(
        "风格化强度",
        options=["轻度", "适中", "重度"],
        value="适中",
        help="轻度=保留原文结构，仅融入语感；适中=全面改写；重度=创作级重写",
    )

    st.sidebar.markdown("---")

    st.sidebar.markdown("### 输出控制")

    enable_word_limit = st.sidebar.checkbox("限制输出字数", value=False)
    target_word_count = None
    if enable_word_limit:
        target_word_count = st.sidebar.number_input(
            "目标字数",
            min_value=50,
            max_value=5000,
            value=500,
            step=50,
        )

    output_mode = st.sidebar.selectbox(
        "输出模式",
        options=["纯文本", "逐段对照", "润色+解析"],
        index=0,
        help="纯文本=直接输出润色结果；逐段对照=原文与润色逐段对比；润色+解析=附带风格运用说明",
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "预设作家：江南 | 村上春树 | 三毛 | 余秋雨 | 毛姆 | 张爱玲 | 鲁迅 | 海明威"
    )

    return {
        "api_key": api_key_input.strip(),
        "api_base": api_base_input.strip(),
        "model": model_name_input.strip(),
        "temperature": temperature,
        "style_intensity": style_intensity,
        "target_word_count": target_word_count,
        "output_mode": output_mode,
    }


def _render_writer_card(writer_name: str):
    desc = WRITER_STYLES.get(writer_name, "")
    if not desc:
        return
    sentences = desc.split("。")
    key_points = [s.strip() + "。" for s in sentences if s.strip()][:3]
    summary = "".join(key_points)
    with st.expander(f"关于 {writer_name} 的风格", expanded=False):
        st.caption(summary)


def _add_to_history(input_text, style, result):
    st.session_state["history"].insert(
        0,
        {
            "input": input_text[:200] + ("..." if len(input_text) > 200 else ""),
            "style": style,
            "result": result,
        },
    )
    if len(st.session_state["history"]) > 20:
        st.session_state["history"] = st.session_state["history"][:20]


def _render_history():
    if not st.session_state.get("history"):
        return

    st.markdown("---")
    st.markdown("### 生成历史")

    for i, item in enumerate(st.session_state["history"]):
        with st.expander(f"#{i + 1}  {item['style']}风格 — {item['input'][:60]}...", expanded=False):
            st.markdown(item["result"])
            if st.button("复制此结果", key=f"copy_{i}"):
                st.code(item["result"], language=None)
            st.markdown("---")


def main():
    st.set_page_config(
        page_title="文风溯源 | Literary Style Transfer",
        page_icon="✍️",
        layout="wide",
    )

    _init_session()

    settings = _render_sidebar()

    col_title, _ = st.columns([3, 1])
    with col_title:
        st.title("✍️ 文风溯源")
        st.caption("Literary Style Transfer — 让你的文字穿越不同作家的灵魂")

    st.markdown("---")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 输入原文")
        input_text = st.text_area(
            "在此粘贴或输入需要润色的文本",
            height=240,
            placeholder="在这里写下你的文字，让 AI 为它披上你钟爱作家的外衣……",
            label_visibility="collapsed",
        )

    with col_right:
        st.markdown("### 选择作家")
        writer_cols = st.columns(4)
        for idx, writer in enumerate(PRESET_WRITERS):
            col_idx = idx % 4
            with writer_cols[col_idx]:
                selected = st.session_state.get("selected_writer", "")
                is_active = selected == writer
                if st.button(
                    writer,
                    key=f"writer_{writer}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state["selected_writer"] = writer

        st.markdown("")
        st.caption("或输入自定义风格：")
        custom_style = st.text_input(
            "自定义作家/风格",
            placeholder="例如：苏轼、马尔克斯、古龙……",
            label_visibility="collapsed",
        )

        selected_writer = st.session_state.get("selected_writer", "")
        if custom_style.strip():
            target_style = custom_style.strip()
        elif selected_writer:
            target_style = selected_writer
        else:
            target_style = PRESET_WRITERS[0]

        if target_style in WRITER_STYLES:
            _render_writer_card(target_style)

        st.markdown("")
        start = st.button("🚀 开始润色", type="primary", use_container_width=True)

    st.markdown("---")

    if start:
        api_key = settings["api_key"]
        if not api_key:
            st.error("❌ 未提供 API Key。请在左侧边栏填写，或在环境变量 OPENAI_API_KEY 中设置。")
            return

        if not input_text.strip():
            st.error("❌ 请输入要润色的文本后再开始。")
            return

        try:
            with st.spinner(f"正在以「{target_style}」风格重写中，请稍候……"):
                result = generate_style_transfer(
                    api_key=api_key,
                    text=input_text,
                    target_style=target_style,
                    temperature=settings["temperature"],
                    style_intensity=settings["style_intensity"],
                    target_word_count=settings["target_word_count"],
                    output_mode=settings["output_mode"],
                    api_base=settings["api_base"] or None,
                    model=settings["model"] or "gpt-3.5-turbo",
                )

            st.success(f"✅ 以「{target_style}」风格润色完成")

            st.markdown("### 润色结果")

            col_result, col_meta = st.columns([4, 1])
            with col_result:
                st.markdown(result)
            with col_meta:
                st.caption(f"风格：{target_style}")
                st.caption(f"模型：{settings['model'] or 'gpt-3.5-turbo'}")
                st.caption(f"强度：{settings['style_intensity']}")
                st.caption(f"创造性：{settings['temperature']}")
                if settings["target_word_count"]:
                    st.caption(f"目标字数：{settings['target_word_count']}")

            _add_to_history(input_text, target_style, result)

            with st.expander("查看原文（对照）", expanded=False):
                st.markdown(input_text)

        except Exception as e:
            st.error(f"❌ 生成失败：{e}")

    _render_history()


if __name__ == "__main__":
    main()