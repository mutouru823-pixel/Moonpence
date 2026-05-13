# Literary-Style-Transfer

文风溯源（Literary-Style-Transfer）是一个轻量的开源工具，用于将用户输入的文本重写为指定作家的文学风格。项目基于 Streamlit 构建，便于本地运行和快速部署。

**主要特性**
- 使用 LLM（OpenAI）进行风格迁移
- 侧边栏可调整 `temperature` 增强创作性
- 支持常见作家预设和自定义风格
- 简洁的 Streamlit UI，适合演示与原型验证

**仓库结构**
- [app.py](app.py): Streamlit 主程序
- [llm_service.py](llm_service.py): 与 LLM API 交互的核心逻辑
- [.env.example](.env.example): 环境变量示例
- [.gitignore](.gitignore): 忽略规则
- [requirements.txt](requirements.txt): Python 依赖

## 快速开始（本地）

1. 克隆仓库并进入目录：

```bash
git clone <your-repo-url>
cd Literary-Style-Transfer
```

2. 建议创建虚拟环境并安装依赖：

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

3. 配置 API Key：
- 复制 `.env.example` 为 `.env` 并填写 `OPENAI_API_KEY`，或直接在侧边栏输入 API Key。

4. 运行 Streamlit 应用：

```bash
streamlit run app.py
```

## 使用说明

1. 在侧边栏填写或粘贴你的 `OPENAI_API_KEY`（如果未在环境变量中配置）。
2. 在主界面输入需要润色的文本。
3. 选择目标作家或输入自定义风格。
4. 可调整 `Temperature`（默认 0.8）以控制生成的创造性。
5. 点击 “开始润色” 等待结果显示。

## 环境变量
- `OPENAI_API_KEY`：你的 OpenAI API Key（可选，通过侧边栏临时输入）。

## 注意事项与扩展
- 当前示例使用 `openai` 官方 SDK，若你希望支持 Google 的 `generativeai`，可在 `llm_service.py` 中替换实现。
- 请遵守所使用 LLM 服务的使用条款与隐私政策。

## 许可证
MIT
# Moonpence