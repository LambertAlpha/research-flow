1. 项目概述 (Executive Summary)
本项目旨在开发一个基于 Web 的内部自动化投研平台。系统将自动抓取 Glassnode Enterprise 及相关金融数据，生成符合公司标准的专业图表，利用 LLM 生成分析草稿，并提供一个交互式界面 (UI) 供分析师进行微调，最终一键导出 PDF 周报。
核心目标： 将周报制作时间从 2天/人 缩短至 30分钟/人。

2. 系统架构 (System Architecture)
系统采用单体 Python 应用架构，分为三层：
数据层 (Data Layer): 负责 API 通信、数据清洗、缓存管理。
逻辑层 (Logic Layer): 负责图表绘制、LLM 提示词组装、PDF 渲染。
交互层 (UI Layer): 基于 Streamlit，提供配置面板、实时预览、Markdown 编辑器。
Code snippet
graph TD
    User[分析师] -->|1. 配置参数| UI[Streamlit 前端界面]
    UI -->|2. 触发生成| Controller[业务逻辑控制器]
    
    subgraph "Data Engine"
        Controller -->|请求数据| API_Mgr[API 管理器]
        API_Mgr -->|Fetch| Glassnode[Glassnode Enterprise]
        API_Mgr -->|Fetch| Coinglass[Coinglass API]
        API_Mgr -->|Fetch| YF[Yahoo Finance]
        API_Mgr -->|Cache| LocalDB[本地缓存 (Pickle/Redis)]
    end
    
    subgraph "Processing"
        Controller -->|原始数据| Plotter[绘图引擎 (Matplotlib)]
        Plotter -->|生成图片| Assets[图片文件夹]
        Controller -->|数据摘要| LLM_Agent[LLM 分析师 Agent]
        LLM_Agent -->|返回 Markdown| UI
    end
    
    User -->|3. 修改文案| UI
    User -->|4. 确认导出| PDF_Engine[PDF 生成器 (WeasyPrint)]
    PDF_Engine -->|读取图片+文案| Report[最终 PDF 周报]


3. 技术栈详细选型 (Tech Stack)
模块
技术组件
选型理由
前端框架
Streamlit
纯 Python 开发，开发速度极快，原生支持 Markdown 编辑和数据展示。
数据请求
requests, yfinance
标准库，稳定可靠。
数据处理
pandas, numpy
金融时间序列处理的标准。
图表绘制
Matplotlib + mplfinance
关键决策：虽然 Plotly 交互性好，但为了生成印刷级 PDF，Matplotlib 静态图更可控（字体、分辨率、水印）。
大模型
LangChain + OpenAI (GPT-4o)
LangChain 用于管理 Prompt 模板；GPT-4o 处理长文本分析。
PDF 生成
Jinja2 + WeasyPrint
将 Markdown 转 HTML 后再转 PDF，支持 CSS 排版，比直接写 PDF 库更灵活美观。


4. 核心模块功能规范
4.1 数据引擎与缓存策略 (Data Engine)
功能： 获取 Glassnode URPD, Cohort, Balance 等数据。
缓存机制 (关键)： 使用 st.cache_data(ttl=3600)。
理由： Glassnode Enterprise 虽然额度高，但请求慢。避免分析师每次刷新页面都重新请求 API，需将数据在本地缓存 1-12 小时。
异常处理： 当 Glassnode API 超时或报错时，自动切换到备用数据源（如 CryptoQuant 免费接口）或返回 "Data Unavailable" 占位符，不让程序崩溃。
4.2 图表工厂 (Chart Factory)
样式标准化： 创建 style.mplstyle 文件，统一定义：
公司品牌色 (Color Palette)。
字体 (推荐 Arial 或 Microsoft YaHei)。
水印 (Watermark)： 所有生成的图片必须在右下角自动添加公司 Logo 透明水印。
输出： 生成高分辨率 PNG (300 DPI) 存入 /temp/images/ 目录。
4.3 交互式编辑器 (Streamlit UI)
左侧侧边栏 (Sidebar)：
选择报告日期范围。
选择重点模块（勾选：宏观、BTC、ETH、山寨）。
语气调节滑块（悲观 <-> 乐观）。
主界面 (Main Area)：
分模块展示： 每个模块（如 BTC 分析）由“图表预览”和“文本编辑器”组成。
Text Area： 预填入 LLM 生成的初稿，分析师可直接修改。
Regenerate 按钮： 仅针对当前段落重新生成。
4.4 报告导出 (PDF Exporter)
流程：
收集用户在界面上最终确认的 Markdown 文本。
读取 /temp/images/ 下的最新图表。
利用 Jinja2 渲染成 HTML（嵌入 CSS 样式，控制页眉、页脚、分页）。
调用 WeasyPrint 将 HTML 渲染为 PDF。
排版要求： 封面必须包含大标题、日期、公司 Logo；正文双栏或单栏排版可配置。

5. 项目目录结构建议
Plaintext
/crypto-report-system
│
├── app.py                   # Streamlit 主入口
├── config.yaml              # 配置文件 (API Keys, 颜色配置)
├── requirements.txt         # 依赖库
│
├── modules/                 # 核心逻辑模块
│   ├── data_fetcher.py      # Glassnode/Yahoo 接口封装
│   ├── chart_builder.py     # Matplotlib 绘图逻辑
│   ├── llm_writer.py        # LangChain Prompt 管理
│   └── pdf_generator.py     # HTML 转 PDF 逻辑
│
├── assets/                  # 静态资源
│   ├── logo.png             # 公司 Logo
│   └── style.css            # PDF 导出样式表
│
├── templates/               # Jinja2 模版
│   └── report_template.html # PDF 的 HTML 骨架
│
└── output/                  # 生成的 PDF 存档


6. 开发分期规划 (Roadmap)
第一阶段：MVP (最小可行性产品) - 预计工期：1周
目标： 跑通 "API -> 数据 -> 简单图表 -> PDF" 流程。
功能：
仅包含 BTC 模块。
不含 LLM，文案使用占位符。
实现 Glassnode 核心数据抓取。
实现 Streamlit 界面展示图表。
第二阶段：接入大脑 (LLM Integration) - 预计工期：1周
目标： 实现自动写稿。
功能：
接入 OpenAI API。
设计 Prompt，让 AI 读取数据并生成分析。
添加 Markdown 编辑器功能。
第三阶段：全功能与美化 - 预计工期：1周
目标： 达到交付标准。
功能：
添加宏观、ETH 模块。
精调图表样式 (Watermark, Color)。
优化 PDF CSS 排版 (封面, 页码)。
部署到公司内部服务器。

7. 给开发者的特别提示 (Tips for Devs)
Glassnode API 坑点： Enterprise 版的某些 endpoints 返回的数据格式较复杂（嵌套 JSON），建议先写一个 notebook 专门测试并解析数据结构。
Prompt 工程： 不要把所有数据一次性扔给 LLM。采用 "分治法" —— 先让 LLM 总结宏观，再总结 BTC，最后拼接。Context Window 有限且容易产生幻觉。
PDF 字体： Linux 服务器上通常没有中文字体，部署时需将 .ttf 字体文件打包进 docker 或项目目录，并在 CSS 中通过 @font-face 引用，否则生成的 PDF 中文会乱码。

