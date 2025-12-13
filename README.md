# Crypto 自动化投研周报系统

> 基于 Python + Streamlit + LangGraph 的加密货币周报自动化生成系统

## 项目概况

本系统旨在将周报制作时间从 2 天缩短至 30 分钟,实现 90% 的数据抓取和图表生成自动化。

**当前版本**: v0.1.0 (MVP - 最小可用产品)

**技术栈**:
- **前端**: Streamlit
- **数据源**: Glassnode, Coinglass, Yahoo Finance
- **图表**: Matplotlib
- **LLM**: OpenAI GPT-4o / Google Gemini
- **Multi-Agent**: LangGraph
- **PDF**: Jinja2 + WeasyPrint

---

## 快速开始

### 1. 环境准备

**Python 版本要求**: Python 3.10+

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Keys

复制 `.env.example` 为 `.env`,并填入你的 API Keys:

```bash
cp .env.example .env
```

编辑 `.env` 文件:

```env
GLASSNODE_API_KEY=your_actual_glassnode_key
COINGLASS_API_KEY=your_actual_coinglass_key
OPENAI_API_KEY=your_actual_openai_key
GEMINI_API_KEY=your_actual_gemini_key  # 可选
```

### 3. 运行应用

```bash
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`

---

## 项目结构

```
research-flow/
├── app.py                      # Streamlit 主界面
├── config.yaml                 # 全局配置文件
├── requirements.txt            # Python 依赖
├── .env                        # API Keys (需自行创建)
│
├── modules/                    # 核心业务逻辑
│   ├── data_fetcher.py         # 数据抓取 (Glassnode, Yahoo Finance)
│   ├── chart_builder.py        # 图表生成工厂
│   ├── utils.py                # 缓存/重试/日志工具
│   ├── llm_writer.py           # LLM 文案生成 (待实现)
│   ├── pdf_generator.py        # PDF 导出 (待实现)
│   ├── agent_state.py          # LangGraph 状态定义 (待实现)
│   ├── agent_nodes.py          # Agent 节点函数 (待实现)
│   └── agent_graph.py          # LangGraph 工作流 (待实现)
│
├── assets/                     # 静态资源
│   ├── style.mplstyle          # Matplotlib 样式
│   ├── logo.png                # 公司 Logo (需自行添加)
│   ├── fonts/                  # 中文字体 (待添加)
│   └── css/                    # PDF 样式 (待添加)
│
├── prompts/                    # LLM Prompt 模板 (待添加)
├── templates/                  # PDF HTML 模板 (待添加)
├── cache/                      # 数据缓存 (自动生成)
├── output/                     # 输出文件 (自动生成)
│   ├── images/                 # 图表 PNG
│   └── reports/                # PDF 报告
│
└── tests/                      # 单元测试 (待添加)
```

---

## 功能清单

### ✅ 已实现 (MVP)

- [x] 项目基础架构搭建
- [x] 数据抓取模块 (Glassnode, Yahoo Finance)
- [x] 图表生成工厂 (BTC 价格, URPD, ETF 流向, 宏观指标)
- [x] 缓存机制 (本地文件缓存, TTL=12小时)
- [x] API 重试机制 (指数退避, 最多3次)
- [x] Streamlit 交互界面 (参数配置, 图表预览)
- [x] Matplotlib 样式配置 (Glassnode 风格)

### 🔨 开发中

- [ ] LLM 文案生成 (GPT-4o + Prompt 模板)
- [ ] LangGraph Multi-Agent 系统
  - [ ] 主编 Agent
  - [ ] 数据工兵 Agent
  - [ ] 图表艺术家 Agent
  - [ ] 资深分析师 Agent
  - [ ] 审核-反驳循环
  - [ ] 辩论机制 (看涨 vs 看跌分析师)
- [ ] PDF 生成与导出
- [ ] Docker 部署
- [ ] 定时任务 (每周自动生成)

### 📋 计划中

- [ ] ETH 深度分析模块
- [ ] 新闻抓取 (CryptoPanic API)
- [ ] 团队协作功能 (草稿保存/加载)
- [ ] 单元测试 (pytest)
- [ ] 性能优化 (并发 API 调用)

---

## 使用指南

### 1. 选择报告模块

在侧边栏勾选你需要的模块:
- **宏观与相关资产**: DXY, US10Y, S&P500, NVDA, COIN
- **BTC 深度分析**: 价格, URPD, ETF 流向, 鲸鱼分群
- **ETH 分析**: ETH/BTC 汇率
- **行业要闻**: Top 新闻 (暂未实现)

### 2. 配置参数

- **日期范围**: 默认最近 30 天
- **均线周期**: 可选 MA10, MA20, MA50, MA100, MA200

### 3. 生成图表

点击 **"🚀 生成图表"** 按钮,系统会自动:
1. 从 API 获取数据 (优先使用缓存)
2. 生成专业图表 (300 DPI PNG)
3. 在界面上展示结果

### 4. 缓存管理

- **查看缓存统计**: 侧边栏显示缓存文件数量和总大小
- **清除缓存**: 点击 "🗑️ 清除所有缓存" 按钮强制重新获取数据

---

## 常见问题

### Q1: 提示 "GLASSNODE_API_KEY 未设置"

**解决方法**: 确保已创建 `.env` 文件并填入有效的 API Key。

```bash
# 检查 .env 文件是否存在
ls -la .env

# 如果不存在,从模板复制
cp .env.example .env

# 编辑并填入真实的 API Key
nano .env
```

### Q2: 图表不显示或报错

**可能原因**:
- API 限流: 等待几分钟后重试
- API Key 无效: 检查 `.env` 配置
- 网络问题: 检查网络连接

**调试方法**:
```bash
# 查看日志文件
tail -f research_flow.log
```

### Q3: 如何添加自己的 Logo?

将你的 Logo 图片 (PNG 格式, 建议尺寸 300x300px) 放到 `assets/logo.png`,系统会自动在图表右下角添加水印。

### Q4: 缓存数据不更新?

点击侧边栏的 **"清除所有缓存"** 按钮,或者手动删除 `cache/` 目录下的文件。

---

## 开发路线图

参见 `/Users/lambertlin/.claude/plans/proud-sleeping-aho.md`

**阶段 1 (当前)**: 基础设施搭建 ✅
**阶段 2**: 图表工厂扩展 (10+ 张图表)
**阶段 3**: LLM 文案生成
**阶段 4**: PDF 导出与 Docker 部署
**阶段 5**: LangGraph Multi-Agent 系统
**阶段 6**: 测试与优化

**预计完成时间**: 6-8 周

---

## 贡献指南

暂不对外开放

---

## 许可证

内部项目,仅供公司使用

---

## 联系方式

技术支持: [Your Email]

---

**更新日期**: 2025-12-13
**版本**: v0.1.0 (MVP)
