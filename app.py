import os
import streamlit as st
from dotenv import load_dotenv

from llm_service import (
    generate_style_transfer,
    WRITER_STYLES,
    analyze_style_samples,
    evaluate_result,
    compute_style_features,
)


load_dotenv()

PRESET_WRITERS = list(WRITER_STYLES.keys())

# 自定义样式
def apply_custom_css():
    st.markdown("""
        <style>
        .main {
            background-color: #fafafa;
        }
        .stButton>button {
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .st-emotion-cache-16idsys p {
            font-size: 14px;
        }
        .st-emotion-cache-1r6slb0 {
            background-color: white;
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        .section-divider {
            margin: 24px 0;
            border: none;
            height: 1px;
            background: linear-gradient(to right, transparent, #e0e0e0, transparent);
        }
        .title-gradient {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .mobile-tip {
            background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);
            padding: 16px;
            border-radius: 12px;
            border-left: 4px solid #667eea;
        }
        </style>
    """, unsafe_allow_html=True)


def _init_session():
    defaults = {
        "history": [],
        "api_key_configured": False,
        "style_samples": "",
        "style_analysis": "",
        "selected_writers": [],
        "last_evaluation": "",
        "iteration_count": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_sidebar():
    with st.sidebar:
        st.markdown("## ⚙️ 配置")
        
        with st.expander("API 设置", expanded=True):
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
                help="DeepSeek / OpenAI / 代理地址，自动补全 /v1",
            )

            env_model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
            model_input = st.text_input(
                "模型名称",
                value=env_model,
                placeholder="deepseek-chat",
                help="例如 deepseek-chat、gpt-4o、qwen-turbo 等",
            )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        
        with st.expander("🎛️ 创作参数", expanded=True):
            temperature = st.slider(
                "创造性 (Temperature)",
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

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        
        with st.expander("📝 输出控制", expanded=True):
            enable_word_limit = st.checkbox("限制输出字数", value=False)
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
                help="纯文本=直接输出润色结果；逐段对照=原文与润色逐段对比；润色+解析=附带风格运用说明",
            )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.caption(
            "预设作家：江南 | 村上春树 | 三毛 | 余秋雨 | 毛姆 | 张爱玲 | 鲁迅 | 海明威"
        )

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

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### 📜 生成历史")

    for i, item in enumerate(st.session_state["history"]):
        with st.expander(f"#{i + 1}  {item['style']}风格 — {item['input'][:60]}...", expanded=False):
            st.markdown(item["result"])
            if st.button("📋 复制此结果", key=f"copy_{i}"):
                st.code(item["result"], language=None)
            st.markdown("---")


def _render_style_comparison(original_text: str, rewritten_text: str):
    try:
        import pandas as pd
        import plotly.express as px

        # 计算风格特征
        orig_features = compute_style_features(original_text)
        rewr_features = compute_style_features(rewritten_text)

        # 创建对比数据框
        comparison_data = []
        for key in orig_features:
            comparison_data.append({
                "指标": key,
                "原文": orig_features[key],
                "润色后": rewr_features[key],
            })

        df = pd.DataFrame(comparison_data)

        # 显示数值对比
        st.markdown("### 📊 风格特征对比")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("平均句长", f"{orig_features['avg_sentence_length']:.1f} 字", f"{rewr_features['avg_sentence_length'] - orig_features['avg_sentence_length']:.1f}")
            st.metric("总字数", f"{orig_features['total_chars']} 字", f"{rewr_features['total_chars'] - orig_features['total_chars']}")
            st.metric("正向词数", orig_features["positive_count"], rewr_features["positive_count"] - orig_features["positive_count"])

        with col2:
            st.metric("总句数", orig_features["total_sentences"], rewr_features["total_sentences"] - orig_features["total_sentences"])
            st.metric("总词数", orig_features["total_words"], rewr_features["total_words"] - orig_features["total_words"])
            st.metric("负向词数", orig_features["negative_count"], rewr_features["negative_count"] - orig_features["negative_count"])

        # 使用 Plotly 创建可视化图表
        st.markdown("### 📈 可视化对比")

        fig = px.bar(
            df.melt(id_vars=["指标"], var_name="文本类型", value_name="数值"),
            x="指标",
            y="数值",
            color="文本类型",
            barmode="group",
            title="原文 vs 润色后 风格特征对比",
            color_discrete_map={"原文": "#1f77b4", "润色后": "#ff7f0e"},
        )
        fig.update_layout(height=450, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        st.info("需安装 pandas 和 plotly 才能查看可视化对比")
    except Exception as e:
        st.error(f"对比分析失败：{e}")


def main():
    st.set_page_config(
        page_title="文风溯源 | Literary Style Transfer",
        page_icon="✍️",
        layout="wide",
    )
    apply_custom_css()

    _init_session()
    settings = _render_sidebar()

    # 标题区域
    st.markdown('<h1 class="title-gradient">✍️ 文风溯源</h1>', unsafe_allow_html=True)
    st.caption("Literary Style Transfer — 让你的文字穿越不同作家的灵魂")
    
    # 手机端使用提示
    with st.expander("📱 手机端使用建议", expanded=False):
        st.markdown("""
        <div class="mobile-tip">
            <p>📌 <strong>添加到主屏幕</strong></p>
            <p><strong>在 iOS (Safari):</strong><br>点击分享按钮 → 选择「添加到主屏幕」</p>
            <p><strong>在 Android (Chrome):</strong><br>点击菜单 → 选择「添加到主屏幕」或「安装应用」</p>
            <p>💡 建议竖屏使用，体验更佳！</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # 主内容区域
    col_left, col_mid, col_right = st.columns([2.5, 1.5, 2])

    with col_left:
        with st.container(border=True):
            st.markdown("### 📝 输入原文")
            input_text = st.text_area(
                "在此粘贴或输入需要润色的文本",
                height=240,
                placeholder="在这里写下你的文字，让 AI 为它披上你钟爱作家的外衣……",
                label_visibility="collapsed",
            )

        st.markdown("")
        
        with st.container(border=True):
            st.markdown("### 📚 风格样本学习")
            st.caption("粘贴目标作家的1-3篇文章片段，让AI学习其独特风格（可选但强烈推荐）")
            style_samples = st.text_area(
                "输入风格样本",
                value=st.session_state.get("style_samples", ""),
                height=120,
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
                                st.success("✅ 风格分析完成！")
                            except Exception as e:
                                st.error(f"分析失败：{e}")
            with col_clear:
                if st.button("🗑️ 清空样本", use_container_width=True):
                    st.session_state["style_samples"] = ""
                    st.session_state["style_analysis"] = ""
                    st.rerun()

            if st.session_state.get("style_analysis"):
                with st.expander("📋 已分析的风格特征", expanded=False):
                    st.success(st.session_state["style_analysis"])

    with col_mid:
        with st.container(border=True):
            st.markdown("### 🎯 选择模式")
            mode = st.radio(
                "选择模式",
                options=["单一作家", "风格混合"],
                index=0,
                label_visibility="collapsed",
                horizontal=True,
            )

        st.markdown("")
        
        with st.container(border=True):
            if mode == "单一作家":
                st.markdown("### ✍️ 选择作家")
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
                    "自定义作家/风格",
                    placeholder="例如：苏轼、马尔克斯、古龙……",
                    label_visibility="collapsed",
                )
            else:
                st.markdown("### 🎨 风格混合")
                st.caption("选择 2-4 位作家，并设置混合比例")
                
                # 选择要混合的作家
                selected_writers = st.multiselect(
                    "选择作家",
                    options=PRESET_WRITERS,
                    default=st.session_state.get("selected_writers", [])[:4],
                    max_selections=4,
                )
                st.session_state["selected_writers"] = selected_writers
                custom_style = ""
                
                # 设置权重
                if selected_writers:
                    total_weight = 0.0
                    weights = {}
                    for i, writer in enumerate(selected_writers):
                        remaining = 100.0 - total_weight
                        default_weight = max(10, remaining / (len(selected_writers) - i))
                        weight = st.slider(
                            f"{writer} 的比例",
                            min_value=10,
                            max_value=100,
                            value=int(default_weight),
                            step=5,
                            key=f"weight_{writer}",
                        )
                        weights[writer] = weight / 100.0
                        total_weight += weight
                    
                    # 归一化
                    total = sum(weights.values())
                    if total > 0:
                        for writer in weights:
                            weights[writer] = weights[writer] / total
                    
                    st.session_state["style_blend"] = weights
                else:
                    st.session_state["style_blend"] = None

        st.markdown("")
        
        # 开始按钮
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
        with st.container(border=True):
            if mode == "单一作家":
                st.markdown("### 📖 作家预览")
                if target_style in WRITER_STYLES:
                    _render_writer_card(target_style)
            elif st.session_state.get("selected_writers"):
                st.markdown("### 🎨 混合预览")
                blend_desc = [f"{writer} ({weight * 100:.0f}%)" for writer, weight in st.session_state.get("style_blend", {}).items()]
                st.success(" + ".join(blend_desc))
                
                for writer in st.session_state["selected_writers"]:
                    _render_writer_card(writer)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # 处理生成
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
                
                with st.spinner(f"正在以「{'混合风格' if style_blend else target_style}」重写中，请稍候……"):
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

                # 显示结果
                display_style = "混合风格" if style_blend else target_style
                st.success(f"✅ 以「{display_style}」风格润色完成")
                st.session_state["iteration_count"] = 0

            except Exception as e:
                st.error(f"❌ 生成失败：{e}")

    # 显示润色结果
    if result_text:
        with st.container(border=True):
            st.markdown("### ✨ 润色结果")

            col_result, col_actions = st.columns([4, 1])
            with col_result:
                st.markdown(result_text)
            with col_actions:
                display_style = "混合风格" if st.session_state.get("style_blend") else target_style
                st.caption(f"**风格：** {display_style}")
                st.caption(f"**强度：** {settings['style_intensity']}")
                st.caption(f"**创造性：** {settings['temperature']}")
                if settings["target_word_count"]:
                    st.caption(f"**目标字数：** {settings['target_word_count']}")
                if st.session_state.get("style_samples"):
                    st.info("✅ 使用了风格样本")
                
                st.markdown("")
                st.button("📋 复制结果", on_click=lambda: st.code(result_text, language=None), use_container_width=True)

                # 评分迭代按钮
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

            _add_to_history(input_text, display_style, result_text)

            with st.expander("📝 查看原文（对照）", expanded=False):
                st.markdown(input_text)

            # 显示风格对比
            _render_style_comparison(input_text, result_text)

    # 显示评分和再润色
    if st.session_state.get("last_evaluation"):
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### 📊 润色评价")
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

    _render_history()


if __name__ == "__main__":
    main()
