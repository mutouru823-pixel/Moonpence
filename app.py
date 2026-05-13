import os
import streamlit as st
from dotenv import load_dotenv

from llm_service import generate_style_transfer


# 加载环境变量（如果存在 .env）
load_dotenv()


def main():
    """Streamlit 主界面入口。"""
    st.set_page_config(page_title="文风溯源 | Literary Style Transfer", layout="centered")

    st.title("文风溯源 | Literary Style Transfer")

    # 侧边栏：API Key 与 LLM 参数
    st.sidebar.header("设置")

    env_api_key = os.environ.get("OPENAI_API_KEY", "")
    api_key_input = st.sidebar.text_input(
        "API Key（若未设置环境变量，请在此处填入）", value=env_api_key, type="password"
    )

    temperature = st.sidebar.slider("Temperature（越高越有创造性）", min_value=0.0, max_value=1.0, value=0.8)

    st.sidebar.markdown("---")
    st.sidebar.markdown("示例作家：村上春树、毛姆、张爱玲、鲁迅、海明威")

    # 主区域：文本输入、目标风格、按钮与输出
    st.subheader("输入原文")
    input_text = st.text_area("在此粘贴或输入需要润色的文本", height=220)

    preset_styles = ["村上春树", "毛姆", "张爱玲", "鲁迅", "海明威", "自定义"]
    target_style_choice = st.selectbox("选择目标作家风格", preset_styles)

    target_style_custom = ""
    if target_style_choice == "自定义":
        target_style_custom = st.text_input("请输入自定义目标作家或风格（例如：莎士比亚风格）")

    target_style = target_style_custom if target_style_custom else target_style_choice

    start = st.button("开始润色")

    if start:
        # 校验 API Key
        api_key = api_key_input.strip()
        if not api_key:
            st.error("未提供 API Key。请在侧边栏填写，或在环境变量 OPENAI_API_KEY 中设置。")
            return

        if not input_text.strip():
            st.error("请输入要润色的文本后再开始。")
            return

        # 调用 LLM 服务进行风格迁移
        try:
            with st.spinner("生成中，请稍候……"):
                result = generate_style_transfer(api_key=api_key, text=input_text, target_style=target_style, temperature=float(temperature))

            st.success("生成完成")
            st.markdown("**润色结果**")
            st.write(result)
        except Exception as e:
            st.error(f"生成失败：{e}")


if __name__ == "__main__":
    main()
