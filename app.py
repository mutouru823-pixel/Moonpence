import os
import streamlit as st
from dotenv import load_dotenv

from llm_service import (
    generate_style_transfer,
    WRITER_STYLES,
    analyze_user_style,
    generate_in_user_style,
    analyze_style_samples,
    evaluate_result,
    save_custom_style,
    get_custom_styles,
    delete_custom_style,
)

load_dotenv()
PRESET_WRITERS = list(WRITER_STYLES.keys())


def _init_session():
    custom_styles = get_custom_styles()
    
    defaults = {
        "history": [],
        "style_samples": "",
        "style_analysis": "",
        "selected_writers": [],
        "last_evaluation": "",
        "iteration_count": 0,
        "user_style_analysis": "",
        "pending_style_name": "",
        "custom_styles": custom_styles,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    st.session_state["custom_styles"] = custom_styles


def main():
    st.set_page_config(
        page_title="文风溯源",
        page_icon="✍️",
        layout="wide",
    )
    
    _init_session()
    settings = _render_sidebar()

    tab1, tab2 = st.tabs(["🎭 风格润色", "✨ 我的写作风格"])

    with tab1:
        _render_style_transfer_tab(settings)

    with tab2:
        _render_user_style_tab(settings)

    _render_history()


def _render_sidebar():
    with st.sidebar:
        st.title("✍️ 文风溯源")
        
        env_api_key = os.environ.get("OPENAI_API_KEY", "")
        env_api_base = os.environ.get("OPENAI_BASE_URL", "")
        env_model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
        
        has_env_config = bool(env_api_key)
        
        if has_env_config:
            st.success("✅ 已从 .env 加载")
        
        with st.expander("⚙️ API 配置", expanded=not has_env_config):
            if not has_env_config:
                st.info("💡 创建 .env 文件可免去每次输入")
                with st.expander("📋 .env 模板", expanded=False):
                    st.code("""OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat""", language="bash")
            
            api_key_input = st.text_input(
                "API Key", value=env_api_key, type="password",
                placeholder="sk-...", disabled=has_env_config,
            )
            api_base_input = st.text_input(
                "API 地址", value=env_api_base,
                placeholder="https://api.deepseek.com",
                disabled=has_env_config,
            )
            model_input = st.text_input(
                "模型", value=env_model,
                placeholder="deepseek-chat",
                disabled=has_env_config,
            )

        with st.expander("🎛️ 创作参数", expanded=False):
            temperature = st.slider("创造性", 0.0, 1.0, 0.8, 0.05)
            style_intensity = st.select_slider(
                "风格化强度",
                options=["轻度", "适中", "重度"],
                value="适中",
            )

        with st.expander("📝 输出控制", expanded=False):
            enable_word_limit = st.checkbox("限制字数")
            target_word_count = None
            if enable_word_limit:
                target_word_count = st.number_input("目标字数", 50, 5000, 500, 50)
            output_mode = st.selectbox("输出模式", ["纯文本", "逐段对照", "润色+解析"])

        st.markdown("---")
        st.caption("预设作家：江南 | 村上春树 | 三毛 | 余秋雨 | 毛姆 | 张爱玲 | 鲁迅 | 海明威")

    return {
        "api_key": api_key_input.strip(),
        "api_base": api_base_input.strip(),
        "model": model_input.strip(),
        "temperature": temperature,
        "style_intensity": style_intensity,
        "target_word_count": target_word_count,
        "output_mode": output_mode,
    }


def _render_style_transfer_tab(settings):
    col_left, col_mid, col_right = st.columns([2.5, 1.5, 2])

    with col_left:
        st.subheader("📝 输入原文")
        input_text = st.text_area(
            "在这里写下你的文字，让 AI 为它披上你钟爱作家的外衣……",
            height=160,
            label_visibility="collapsed",
        )
        st.session_state["input_text"] = input_text

        st.divider()

        st.subheader("📚 风格样本学习")
        style_samples = st.text_area(
            "粘贴《龙族》《挪威的森林》等你喜欢的作家作品片段……",
            height=90,
            label_visibility="collapsed",
        )
        st.session_state["style_samples"] = style_samples

        col_analyze, col_clear = st.columns(2)
        with col_analyze:
            if st.button("🔍 分析样本风格", type="primary", use_container_width=True):
                if not settings["api_key"]:
                    st.error("请先在左侧设置 API Key")
                elif not style_samples.strip():
                    st.error("请先输入风格样本")
                else:
                    with st.spinner("正在分析样本风格……"):
                        try:
                            analysis = analyze_style_samples(
                                api_key=settings["api_key"],
                                api_base=settings["api_base"],
                                model=settings["model"] or "gpt-3.5-turbo",
                                samples=style_samples,
                            )
                            st.session_state["style_analysis"] = analysis
                            st.success("✅ 风格分析完成！")
                        except Exception as e:
                            st.error(f"分析失败：{e}")
        with col_clear:
            if st.button("🗑️ 清空", use_container_width=True):
                st.session_state["style_samples"] = ""
                st.session_state["style_analysis"] = ""
                st.rerun()

        st.divider()

        st.subheader("💾 保存为自定义风格")
        st.caption("将分析结果或手动输入的风格描述保存，方便以后使用")
        
        if st.session_state.get("style_analysis"):
            st.success("已分析的风格：" + st.session_state["style_analysis"][:100] + "...")
        
        style_source = st.radio(
            "选择风格描述来源",
            ["使用AI分析结果", "手动输入风格描述"],
            horizontal=True,
        )
        
        style_description = ""
        if style_source == "使用AI分析结果":
            if st.session_state.get("style_analysis"):
                style_description = st.session_state["style_analysis"]
                st.caption("✅ 将使用上方AI分析出的风格特征")
            else:
                st.warning("⚠️ 还没有分析结果，请先分析或切换到手动输入")
        else:
            style_description = st.text_area(
                "✍️ 手动描述风格特征",
                height=80,
                placeholder="描述你想要的风格，例如：文风华丽细腻，擅长用繁复的比喻……",
            )
        
        st.divider()
        
        col_name, col_btn = st.columns([3, 1])
        with col_name:
            custom_style_name = st.text_input(
                "🎨 给风格起个名字",
                placeholder="例如：金庸风格、我的文风……",
            )
        with col_btn:
            st.markdown("")
            if st.button("💾 保存", type="primary", use_container_width=True):
                if not custom_style_name.strip():
                    st.error("请输入风格名称！")
                elif not style_description.strip():
                    st.error("风格描述为空！")
                else:
                    if save_custom_style(custom_style_name.strip(), style_description):
                        st.success(f"🎉 成功保存「{custom_style_name}」！")
                        st.session_state["custom_styles"] = get_custom_styles()
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("保存失败！")

    with col_mid:
        st.subheader("🎯 选择模式")
        mode = st.radio("", ["单一作家", "风格混合"], horizontal=True, label_visibility="collapsed")
        
        st.divider()
        
        custom_styles = st.session_state.get("custom_styles", {})
        all_writers = PRESET_WRITERS + list(custom_styles.keys())
        
        if mode == "单一作家":
            st.subheader("✍️ 选择作家")
            
            if custom_styles:
                st.markdown("**⭐ 我的自定义风格**")
                for style_name in custom_styles.keys():
                    selected = st.session_state.get("selected_writer", "")
                    btn_type = "primary" if selected == style_name else "secondary"
                    if st.button(f"⭐ {style_name}", key=f"custom_{style_name}", use_container_width=True, type=btn_type):
                        st.session_state["selected_writer"] = style_name
                
                with st.expander("🗑️ 管理自定义风格"):
                    for style_name in list(custom_styles.keys()):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.text(f"📝 {style_name}")
                        with col2:
                            if st.button("删除", key=f"del_{style_name}"):
                                delete_custom_style(style_name)
                                st.session_state["custom_styles"] = get_custom_styles()
                                st.rerun()
                
                st.markdown("**📚 预设作家风格**")
            
            for writer in PRESET_WRITERS:
                selected = st.session_state.get("selected_writer", "")
                btn_type = "primary" if selected == writer else "secondary"
                if st.button(writer, key=f"writer_{writer}", use_container_width=True, type=btn_type):
                    st.session_state["selected_writer"] = writer
            
            st.markdown("*或输入自定义：*")
            custom_style_input = st.text_input("自定义风格", placeholder="例如：苏轼、古龙……", label_visibility="collapsed")
        else:
            st.subheader("🎨 风格混合")
            selected_writers = st.multiselect("选择作家", options=all_writers, max_selections=4)
            st.session_state["selected_writers"] = selected_writers
            custom_style_input = ""
            
            if selected_writers:
                weights = {}
                for writer in selected_writers:
                    weights[writer] = st.slider(f"{writer} 的比例", 10, 100, 50, 5) / 100.0
                total = sum(weights.values())
                if total > 0:
                    weights = {w: v/total for w, v in weights.items()}
                st.session_state["style_blend"] = weights
            else:
                st.session_state["style_blend"] = None

        st.divider()
        
        if mode == "单一作家":
            selected_writer = st.session_state.get("selected_writer", "")
            target_style = custom_style_input.strip() or selected_writer or PRESET_WRITERS[0]
        else:
            target_style = ""
        
        if st.button("🚀 开始润色", type="primary", use_container_width=True):
            _handle_style_transfer(settings, mode, target_style)

    with col_right:
        st.subheader("📖 预览与参考")
        custom_styles = st.session_state.get("custom_styles", {})
        
        if mode == "单一作家" and target_style:
            if target_style in WRITER_STYLES:
                _render_writer_info(target_style)
            elif target_style in custom_styles:
                st.info(custom_styles[target_style])
        elif mode == "风格混合" and st.session_state.get("selected_writers"):
            blend_names = []
            for w in st.session_state["selected_writers"]:
                blend_names.append("⭐" + w if w in custom_styles else w)
            st.success(" + ".join(blend_names))
            for w in st.session_state["selected_writers"]:
                if w in WRITER_STYLES:
                    _render_writer_info(w)

    st.divider()
    
    if "result_text" in st.session_state and st.session_state["result_text"]:
        st.subheader("✨ 润色结果")
        display_style = st.session_state.get("display_style", "")
        st.markdown(f"**风格：** {display_style}")
        st.markdown(st.session_state["result_text"])
        st.button("📋 复制结果", on_click=lambda: st.code(st.session_state["result_text"]))


def _handle_style_transfer(settings, mode, target_style):
    if not settings["api_key"]:
        st.error("❌ 未提供 API Key")
        return
    if not st.session_state.get("input_text", "").strip():
        st.error("❌ 请输入要润色的文本")
        return
    if mode == "风格混合" and len(st.session_state.get("selected_writers", [])) < 2:
        st.error("❌ 风格混合需要至少2位作家")
        return
    
    try:
        style_blend = st.session_state.get("style_blend") if mode == "风格混合" else None
        with st.spinner(f"正在以「{'混合风格' if style_blend else target_style}」重写中……"):
            result_text = generate_style_transfer(
                api_key=settings["api_key"],
                text=st.session_state["input_text"],
                target_style=target_style,
                temperature=settings["temperature"],
                style_intensity=settings["style_intensity"],
                target_word_count=settings["target_word_count"],
                output_mode=settings["output_mode"],
                api_base=settings["api_base"] or None,
                model=settings["model"] or "gpt-3.5-turbo",
                style_samples=st.session_state.get("style_samples"),
                style_analysis=st.session_state.get("style_analysis"),
                style_blend=style_blend,
            )
        
        st.session_state["result_text"] = result_text
        st.session_state["display_style"] = "混合风格" if style_blend else target_style
        st.success(f"✅ 以「{st.session_state['display_style']}」风格润色完成！")
        st.rerun()
    except Exception as e:
        st.error(f"❌ 生成失败：{e}")


def _render_writer_info(writer_name):
    desc = WRITER_STYLES.get(writer_name, "")
    if desc:
        with st.expander(f"📖 关于 {writer_name}", expanded=False):
            st.info(desc[:200])


def _render_user_style_tab(settings):
    st.subheader("🔍 分析我的写作风格")
    st.caption("提供你写的文本，AI将分析你的个人写作风格特征")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        user_texts = st.text_area(
            "粘贴你写的2-5篇文本，用 --- 分隔",
            height=180,
            label_visibility="collapsed",
        )
    with col2:
        st.markdown("")
        st.markdown("")
        if st.button("🔬 分析我的风格", type="primary", use_container_width=True):
            if not settings["api_key"]:
                st.error("请先在左侧设置 API Key")
            elif not user_texts.strip():
                st.error("请先输入你的文本")
            else:
                texts = [t.strip() for t in user_texts.split("---") if t.strip()]
                with st.spinner("正在分析你的写作风格……"):
                    try:
                        analysis = analyze_user_style(
                            api_key=settings["api_key"],
                            api_base=settings["api_base"],
                            model=settings["model"] or "gpt-3.5-turbo",
                            user_texts=texts,
                        )
                        st.session_state["user_style_analysis"] = analysis
                        st.success("✅ 风格分析完成！")
                    except Exception as e:
                        st.error(f"分析失败：{e}")

    if st.session_state.get("user_style_analysis"):
        st.divider()
        st.subheader("📋 你的写作风格分析报告")
        st.success(st.session_state["user_style_analysis"])
        
        st.divider()
        st.subheader("✍️ 用你的风格写作")
        
        col_topic, col_genre = st.columns([3, 1])
        with col_topic:
            topic = st.text_input("写作主题", placeholder="例如：关于秋天的记忆……")
        with col_genre:
            genre = st.selectbox("体裁", ["散文", "随笔", "日记", "小说片段", "诗歌"])
        
        if st.button("📝 开始写作", type="primary", use_container_width=True):
            if not settings["api_key"]:
                st.error("请先在左侧设置 API Key")
            elif not topic.strip():
                st.error("请输入写作主题")
            else:
                with st.spinner("正在用你的风格写作……"):
                    try:
                        result = generate_in_user_style(
                            api_key=settings["api_key"],
                            api_base=settings["api_base"],
                            model=settings["model"] or "gpt-3.5-turbo",
                            user_style_analysis=st.session_state["user_style_analysis"],
                            topic=topic,
                            genre=genre,
                        )
                        st.success("✅ 写作完成！")
                        st.markdown(f"### 📜 {genre}：{topic}")
                        st.markdown(result)
                        st.button("📋 复制全文", on_click=lambda: st.code(result))
                    except Exception as e:
                        st.error(f"写作失败：{e}")


def _render_history():
    if not st.session_state.get("history"):
        return
    
    st.divider()
    st.subheader("📜 生成历史")
    
    for i, item in enumerate(st.session_state["history"]):
        with st.expander(f"#{i + 1}  {item['style']}风格 — {item['input'][:60]}...", expanded=False):
            st.markdown(item["result"])


if __name__ == "__main__":
    main()
