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
    defaults = {
        "history": [],
        "style_samples": "",
        "style_analysis": "",
        "selected_writers": [],
        "last_evaluation": "",
        "iteration_count": 0,
        "user_style_analysis": "",
        "pending_style_name": "",
        "custom_styles": get_custom_styles(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_custom_css():
    st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    
    .stButton>button {
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.2s ease;
        border: 1px solid #cbd5e1;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    h1, h2, h3 {
        font-weight: 600 !important;
    }
    
    .card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        border: 3px solid #e2e8f0;
        margin-bottom: 28px;
        position: relative;
    }
    
    .card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 16px 16px 0 0;
    }
    
    .card-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 3px solid #f1f5f9;
        color: #1e293b;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .card-desc {
        color: #64748b;
        font-size: 14px;
        margin-bottom: 20px;
        line-height: 1.6;
    }
    
    .sidebar-logo {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 24px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
        border: 2px solid rgba(255,255,255,0.2);
    }
    
    .section-divider {
        height: 24px;
        background: transparent;
        margin: 8px 0;
    }
    
    .tab-content {
        padding: 20px 0;
    }
    
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column"] > [data-testid="stVerticalBlock"] {
        gap: 28px;
    }
    </style>
    """, unsafe_allow_html=True)


def _render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <h2 style="font-size: 22px; margin-bottom: 4px;">文风溯源</h2>
            <p style="font-size: 13px; opacity: 0.9; margin: 0;">Literary Style Transfer</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("⚙️ API 配置", expanded=True):
            env_api_key = os.environ.get("OPENAI_API_KEY", "")
            api_key_input = st.text_input(
                "API Key",
                value=env_api_key,
                type="password",
                placeholder="sk-...",
                help="若不设置环境变量，请在此填入 API Key",
            )

            env_api_base = os.environ.get("OPENAI_BASE_URL", "")
            api_base_input = st.text_input(
                "API 地址",
                value=env_api_base,
                placeholder="https://api.deepseek.com",
            )

            env_model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
            model_input = st.text_input(
                "模型名称",
                value=env_model,
                placeholder="deepseek-chat",
            )

        with st.expander("🎛️ 创作参数", expanded=False):
            temperature = st.slider(
                "创造性",
                min_value=0.0,
                max_value=1.0,
                value=0.8,
                step=0.05,
                help="越高越有创造性，越低越稳定保守",
            )

            style_intensity = st.select_slider(
                "风格化强度",
                options=["轻度", "适中", "重度"],
                value="适中",
                help="轻度=保留原文结构，仅融入语感；适中=全面改写；重度=创作级重写",
            )

        with st.expander("📝 输出控制", expanded=False):
            enable_word_limit = st.checkbox("限制字数", value=False)
            target_word_count = None
            if enable_word_limit:
                target_word_count = st.number_input(
                    "目标字数",
                    min_value=50,
                    max_value=5000,
                    value=500,
                    step=50,
                )

            output_mode = st.selectbox(
                "输出模式",
                options=["纯文本", "逐段对照", "润色+解析"],
                index=0,
            )

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


def _render_writer_card(writer_name: str):
    desc = WRITER_STYLES.get(writer_name, "")
    if not desc:
        return
    sentences = desc.split("。")
    key_points = [s.strip() + "。" for s in sentences if s.strip()][:3]
    summary = "".join(key_points)
    with st.expander(f"📖 关于 {writer_name} 的风格", expanded=False):
        st.info(summary)


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

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div class="card">
            <div class="card-title">📜 生成历史</div>
        """, unsafe_allow_html=True)

        for i, item in enumerate(st.session_state["history"]):
            with st.expander(f"#{i + 1}  {item['style']}风格 — {item['input'][:60]}...", expanded=False):
                st.markdown(item["result"])
                if st.button("📋 复制此结果", key=f"copy_{i}"):
                    st.code(item["result"], language=None)
                st.markdown("---")
        
        st.markdown('</div>', unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="文风溯源",
        page_icon="✍️",
        layout="wide",
    )
    apply_custom_css()
    _init_session()
    settings = _render_sidebar()

    tab1, tab2 = st.tabs(["🎭 风格润色", "✨ 我的写作风格"])

    with tab1:
        col_left, col_mid, col_right = st.columns([2.5, 1.5, 2])

        with col_left:
            # 输入原文卡片
            with st.container():
                st.markdown("""
                <div class="card">
                    <div class="card-title">📝 输入原文</div>
                    <div class="card-desc">把你想要润色的文字粘贴在这里</div>
                </div>
                """, unsafe_allow_html=True)
                
                input_text = st.text_area(
                    "",
                    height=160,
                    placeholder="在这里写下你的文字，让 AI 为它披上你钟爱作家的外衣……",
                    label_visibility="collapsed",
                )

            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            
            # 风格样本学习卡片
            with st.container():
                st.markdown("""
                <div class="card">
                    <div class="card-title">📚 风格样本学习</div>
                    <div class="card-desc">粘贴目标作家的1-3篇文章片段，让AI学习其独特风格（可选）</div>
                """, unsafe_allow_html=True)
                
                style_samples = st.text_area(
                    "",
                    value=st.session_state.get("style_samples", ""),
                    height=90,
                    placeholder="粘贴《龙族》《挪威的森林》等你喜欢的作家作品片段……",
                    label_visibility="collapsed",
                )
                st.session_state["style_samples"] = style_samples

                col_analyze, col_clear = st.columns([1, 1])
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
                                    st.session_state["pending_style_name"] = ""
                                    st.success("✅ 风格分析完成！请设置风格名称并保存")
                                except Exception as e:
                                    st.error(f"分析失败：{e}")
                with col_clear:
                    if st.button("🗑️ 清空", use_container_width=True):
                        st.session_state["style_samples"] = ""
                        st.session_state["style_analysis"] = ""
                        st.session_state["pending_style_name"] = ""
                        st.rerun()

                if st.session_state.get("style_analysis"):
                    with st.expander("📋 已分析的风格特征", expanded=False):
                        st.success(st.session_state["style_analysis"])
                    
                    st.markdown("---")
                    st.markdown("### 💾 保存为自定义风格")
                    
                    col_name, col_save = st.columns([2, 1])
                    with col_name:
                        custom_style_name = st.text_input(
                            "🎨 风格名称",
                            value=st.session_state.get("pending_style_name", ""),
                            placeholder="给你的风格起个名字，如：我的文风、金庸风格……",
                            help="输入风格名称后保存，之后可在作家列表中使用"
                        )
                        st.session_state["pending_style_name"] = custom_style_name
                    
                    with col_save:
                        st.markdown("")
                        if st.button("💾 保存此风格", type="primary", use_container_width=True):
                            if not custom_style_name.strip():
                                st.error("请输入风格名称")
                            else:
                                if save_custom_style(custom_style_name.strip(), st.session_state["style_analysis"]):
                                    st.success(f"✅ 已保存风格「{custom_style_name}」")
                                    st.session_state["custom_styles"] = get_custom_styles()
                                    st.rerun()
                                else:
                                    st.error("保存失败，请重试")
                
                st.markdown('</div>', unsafe_allow_html=True)

        with col_mid:
            # 模式选择卡片
            with st.container():
                st.markdown("""
                <div class="card">
                    <div class="card-title">🎯 选择模式</div>
                """, unsafe_allow_html=True)
                
                mode = st.radio(
                    "",
                    options=["单一作家", "风格混合"],
                    index=0,
                    label_visibility="collapsed",
                    horizontal=True,
                )
                
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            
            # 作家选择/风格混合卡片
            with st.container():
                st.markdown("""
                <div class="card">
                """, unsafe_allow_html=True)
                
                custom_styles = st.session_state.get("custom_styles", {})
                all_writers = PRESET_WRITERS + list(custom_styles.keys())
                
                if mode == "单一作家":
                    st.markdown("### ✍️ 选择作家")
                    
                    if custom_styles:
                        st.markdown("#### 🎨 我的自定义风格")
                        custom_cols = st.columns(2)
                        for idx, style_name in enumerate(custom_styles.keys()):
                            col_idx = idx % 2
                            with custom_cols[col_idx]:
                                selected = st.session_state.get("selected_writer", "")
                                is_active = selected == style_name
                                if st.button(
                                    f"⭐ {style_name}",
                                    key=f"single_custom_{style_name}",
                                    use_container_width=True,
                                    type="primary" if is_active else "secondary",
                                ):
                                    st.session_state["selected_writer"] = style_name
                                    st.session_state["selected_writers"] = []
                        
                        with st.expander("🗑️ 管理自定义风格", expanded=False):
                            for style_name in list(custom_styles.keys()):
                                col_del_name, col_del_btn = st.columns([3, 1])
                                with col_del_name:
                                    st.text(f"📝 {style_name}")
                                with col_del_btn:
                                    if st.button("删除", key=f"del_{style_name}"):
                                        delete_custom_style(style_name)
                                        st.session_state["custom_styles"] = get_custom_styles()
                                        if st.session_state.get("selected_writer") == style_name:
                                            st.session_state["selected_writer"] = ""
                                        st.rerun()
                        
                        st.markdown("")
                        st.markdown("#### 📚 预设作家风格")
                    
                    writer_cols = st.columns(2)
                    for idx, writer in enumerate(PRESET_WRITERS):
                        col_idx = idx % 2
                        with writer_cols[col_idx]:
                            selected = st.session_state.get("selected_writer", "")
                            is_active = selected == writer
                            if st.button(
                                writer,
                                key=f"single_writer_{writer}",
                                use_container_width=True,
                                type="primary" if is_active else "secondary",
                            ):
                                st.session_state["selected_writer"] = writer
                                st.session_state["selected_writers"] = []

                    st.markdown("")
                    st.caption("或输入自定义风格：")
                    custom_style = st.text_input(
                        "",
                        placeholder="例如：苏轼、马尔克斯、古龙……",
                        label_visibility="collapsed",
                    )
                else:
                    st.markdown("### 🎨 风格混合")
                    st.caption("选择 2-4 位作家，并设置混合比例")
                    
                    selected_writers = st.multiselect(
                        "选择作家",
                        options=all_writers,
                        default=st.session_state.get("selected_writers", [])[:4],
                        max_selections=4,
                    )
                    st.session_state["selected_writers"] = selected_writers
                    custom_style = ""
                    
                    if selected_writers:
                        weights = {}
                        for writer in selected_writers:
                            weight = st.slider(
                                f"{writer} 的比例",
                                min_value=10,
                                max_value=100,
                                value=50,
                                step=5,
                                key=f"weight_{writer}",
                            )
                            weights[writer] = weight / 100.0
                        
                        total = sum(weights.values())
                        if total > 0:
                            for writer in weights:
                                weights[writer] = weights[writer] / total
                        
                        st.session_state["style_blend"] = weights
                    else:
                        st.session_state["style_blend"] = None
                
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            
            if mode == "单一作家":
                selected_writer = st.session_state.get("selected_writer", "")
                if custom_style.strip():
                    target_style = custom_style.strip()
                elif selected_writer:
                    target_style = selected_writer
                else:
                    target_style = PRESET_WRITERS[0]
            else:
                target_style = ""

            start = st.button("🚀 开始润色", type="primary", use_container_width=True)

        with col_right:
            # 作家预览卡片
            with st.container():
                st.markdown("""
                <div class="card">
                    <div class="card-title">📖 预览与参考</div>
                """, unsafe_allow_html=True)
                
                custom_styles = st.session_state.get("custom_styles", {})
                
                if mode == "单一作家":
                    st.markdown("#### 作家风格介绍")
                    if target_style in WRITER_STYLES:
                        _render_writer_card(target_style)
                    elif target_style in custom_styles:
                        with st.expander(f"📝 自定义风格「{target_style}」", expanded=True):
                            st.info(custom_styles[target_style])
                elif st.session_state.get("selected_writers"):
                    st.markdown("#### 风格混合预览")
                    blend_desc = []
                    for writer in st.session_state["selected_writers"]:
                        if writer in custom_styles:
                            blend_desc.append(f"⭐{writer}")
                        else:
                            blend_desc.append(writer)
                    st.success(" + ".join(blend_desc))
                    
                    for writer in st.session_state["selected_writers"]:
                        if writer in WRITER_STYLES:
                            _render_writer_card(writer)
                        else:
                            with st.expander(f"📝 {writer}", expanded=False):
                                st.info(custom_styles.get(writer, ""))
                
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        result_text = ""
        if start:
            api_key = settings["api_key"]
            if not api_key:
                st.error("❌ 未提供 API Key。请在左侧设置中填写，或在环境变量 OPENAI_API_KEY 中设置。")
            elif not input_text.strip():
                st.error("❌ 请输入要润色的文本后再开始。")
            elif mode == "风格混合" and len(st.session_state.get("selected_writers", [])) < 2:
                st.error("❌ 风格混合模式需要选择至少 2 位作家。")
            else:
                try:
                    style_blend = st.session_state.get("style_blend") if mode == "风格混合" else None
                    
                    with st.spinner(f"正在以「{'混合风格' if style_blend else target_style}」重写中……"):
                        result_text = generate_style_transfer(
                            api_key=api_key,
                            text=input_text,
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

                    display_style = "混合风格" if style_blend else target_style
                    st.success(f"✅ 以「{display_style}」风格润色完成")
                    st.session_state["iteration_count"] = 0

                except Exception as e:
                    st.error(f"❌ 生成失败：{e}")

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        if result_text:
            with st.container():
                st.markdown("""
                <div class="card">
                    <div class="card-title">✨ 润色结果</div>
                """, unsafe_allow_html=True)

                col_result, col_actions = st.columns([4, 1])
                with col_result:
                    st.markdown(result_text)
                with col_actions:
                    display_style = "混合风格" if st.session_state.get("style_blend") else target_style
                    st.caption(f"**风格：** {display_style}")
                    st.caption(f"**强度：** {settings['style_intensity']}")
                    if settings["target_word_count"]:
                        st.caption(f"**目标字数：** {settings['target_word_count']}")
                    
                    st.markdown("")
                    st.button("📋 复制结果", on_click=lambda: st.code(result_text, language=None), use_container_width=True)

                    st.markdown("")
                    if st.button("🔍 评分并优化", type="secondary", use_container_width=True):
                        with st.spinner("正在评估润色结果……"):
                            try:
                                style_blend = st.session_state.get("style_blend")
                                evaluation = evaluate_result(
                                    api_key=settings["api_key"],
                                    api_base=settings["api_base"],
                                    model=settings["model"] or "gpt-3.5-turbo",
                                    original_text=input_text,
                                    rewritten_text=result_text,
                                    target_style=target_style,
                                    style_blend=style_blend,
                                )
                                st.session_state["last_evaluation"] = evaluation
                                st.success("评估完成！")
                            except Exception as e:
                                st.error(f"评估失败：{e}")
                
                st.markdown('</div>', unsafe_allow_html=True)

                _add_to_history(input_text, display_style, result_text)

                with st.expander("📝 查看原文（对照）", expanded=False):
                    st.markdown(input_text)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        if st.session_state.get("last_evaluation"):
            with st.container():
                st.markdown("""
                <div class="card">
                    <div class="card-title">📊 润色评价</div>
                """, unsafe_allow_html=True)
                
                st.info(st.session_state["last_evaluation"])
                
                col_retry, col_clear = st.columns([1, 1])
                with col_retry:
                    if st.button("🔄 根据建议再润色", type="primary", use_container_width=True):
                        with st.spinner("正在根据反馈优化润色……"):
                            try:
                                style_blend = st.session_state.get("style_blend")
                                result_text = generate_style_transfer(
                                    api_key=settings["api_key"],
                                    text=input_text,
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
                                    evaluation_feedback=st.session_state["last_evaluation"],
                                )
                                st.session_state["iteration_count"] += 1
                                st.success(f"再润色完成！（迭代次数：{st.session_state['iteration_count']}）")
                                st.rerun()
                            except Exception as e:
                                st.error(f"再润色失败：{e}")
                with col_clear:
                    if st.button("🗑️ 清除评价", use_container_width=True):
                        st.session_state["last_evaluation"] = ""
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        # 风格分析卡片
        with st.container():
            st.markdown("""
            <div class="card">
                <div class="card-title">🔍 分析我的写作风格</div>
                <div class="card-desc">提供你写的 2-5 篇文本，AI 将分析你的个人写作风格特征</div>
            """, unsafe_allow_html=True)
        
        col_sample1, col_sample2 = st.columns([3, 1])
        
        with col_sample1:
            user_texts_input = st.text_area(
                "",
                value=st.session_state.get("user_texts_input", ""),
                height=180,
                placeholder="粘贴你写的2-5篇文本，用 --- 分隔不同文章……",
                label_visibility="collapsed",
            )
            st.session_state["user_texts_input"] = user_texts_input
            
        with col_sample2:
            st.markdown("")
            st.markdown("")
            if st.button("🔬 分析我的风格", type="primary", use_container_width=True):
                if not settings["api_key"]:
                    st.error("请先在左侧设置 API Key")
                elif not user_texts_input.strip():
                    st.error("请先输入你的文本")
                else:
                    texts = [t.strip() for t in user_texts_input.split("---") if t.strip()]
                    if len(texts) < 1:
                        st.error("请至少提供一篇文本")
                    else:
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
        
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        if st.session_state.get("user_style_analysis"):
            # 风格分析结果卡片
            with st.container():
                st.markdown("""
                <div class="card">
                    <div class="card-title">📋 你的写作风格分析报告</div>
                """, unsafe_allow_html=True)
                
                st.success(st.session_state["user_style_analysis"])
                
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            
            # 用我的风格写作卡片
            with st.container():
                st.markdown("""
                <div class="card">
                    <div class="card-title">✍️ 用你的风格写作</div>
                    <div class="card-desc">基于分析出的风格特征，帮你撰写符合你个人风格的文章</div>
                """, unsafe_allow_html=True)

                col_topic, col_genre = st.columns([3, 1])
                
                with col_topic:
                    topic = st.text_input(
                        "",
                        placeholder="例如：关于秋天的记忆、一次难忘的旅行……",
                        label_visibility="collapsed",
                    )
                
                with col_genre:
                    genre = st.selectbox(
                        "文章体裁",
                        options=["散文", "随笔", "日记", "小说片段", "诗歌"],
                        index=0,
                    )

                writing_temperature = st.slider(
                    "创造性",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.05,
                    help="控制写作的创造性程度",
                )

                enable_write_limit = st.checkbox("限制字数", value=False)
                write_word_count = None
                if enable_write_limit:
                    write_word_count = st.number_input(
                        "目标字数",
                        min_value=100,
                        max_value=3000,
                        value=800,
                        step=100,
                    )

                if st.button("📝 开始写作", type="primary", use_container_width=True):
                    if not settings["api_key"]:
                        st.error("请先在左侧设置 API Key")
                    elif not topic.strip():
                        st.error("请输入写作主题")
                    else:
                        with st.spinner("正在用你的风格写作……"):
                            try:
                                written_result = generate_in_user_style(
                                    api_key=settings["api_key"],
                                    api_base=settings["api_base"],
                                    model=settings["model"] or "gpt-3.5-turbo",
                                    user_style_analysis=st.session_state["user_style_analysis"],
                                    topic=topic,
                                    genre=genre,
                                    target_word_count=write_word_count,
                                    temperature=writing_temperature,
                                )
                                
                                st.success("✅ 写作完成！")
                                
                                # 写作结果卡片
                                with st.container():
                                    st.markdown('<div class="card">', unsafe_allow_html=True)
                                    st.markdown(f"### 📜 {genre}：{topic}")
                                    st.markdown(written_result)
                                    
                                    _add_to_history(f"【写作】{topic}", "个人风格", written_result)
                                    
                                    st.button("📋 复制全文", on_click=lambda: st.code(written_result, language=None), use_container_width=True)
                                    
                                    st.markdown('</div>', unsafe_allow_html=True)
                                    
                            except Exception as e:
                                st.error(f"写作失败：{e}")
                
                st.markdown('</div>', unsafe_allow_html=True)

    _render_history()


if __name__ == "__main__":
    main()
