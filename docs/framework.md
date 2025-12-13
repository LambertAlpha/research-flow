Crypto 自动化投研周报标准化框架 (V3.0)
版本： V3.0 (Glassnode Enterprise Edition)
适用对象： 投研团队、开发工程师
目标： 实现从数据抓取、图表绘制到文案生成的全流程自动化，对标顶级投研机构手工周报。

一、 总体架构 (Architecture)
本系统基于 "Data + LLM" 模式。通过 Python 脚本调用企业级 API 获取数据，绘制专业图表，并投喂给大语言模型（GPT-4o/Claude 3.5）生成类人风格的分析报告。
核心数据源：
链上/资金数据： Glassnode (Enterprise), Coinglass API (Premium).
宏观/行情数据： Yahoo Finance (yfinance), CCXT (交易所接口), Financial Modeling Prep (FMP).
新闻舆情： CryptoPanic API.
输出格式： PDF 报告 (包含 Matplotlib/Plotly 绘制的图表 + Markdown 排版文案).

二、 模块详细定义 (Modules Specification)
模块 0：执行摘要 (Executive Summary) —— 宏观前瞻
功能： 确立报告的宏观基调，连接过去与未来。
自动化逻辑：
本周回顾： 抓取本周发布的 CPI/非农/利率决议等 "High Impact" 事件的公布值 vs 预测值，结合 BTC 价格波动，让 LLM 总结影响。
下周前瞻： 调用财经日历 API，列出下周 Top 3 关键事件（如 FOMC 会议、NVDA 财报、ETH 升级）。
核心观点： 基于下方模型的定量评分，给出最终的多空倾向（Bullish / Bearish / Neutral）。
关键数据源： FMP API (经济日历), CryptoPanic (新闻热度).
模块 1：宏观与相关资产 (Macro & TradFi)
分析维度： 外部流动性环境。
数据指标 (Data Points)：
美股风向： Nasdaq 100, S&P 500, Russell 2000 涨跌幅及与 MA50 的距离。
关键个股： Nvidia (NVDA), Coinbase (COIN), MicroStrategy (MSTR) 价格行为。
宏观因子： 美元指数 (DXY), 10年期美债收益率 (US10Y), 黄金 (Gold)。
分析逻辑： 若 DXY 突破上行通道且美债收益率走高 -> 判定为流动性紧缩（利空 Crypto）。
数据源： yfinance (免费且稳定).
模块 2：BTC 深度分析 (BTC Deep Dive) —— 核心
分析维度： 结合链上筹码与衍生品市场。
关键图表与指标 (复刻原版周报)：
价量结构： K线形态 + 关键均线 (MA50/200) + 支撑阻力位。
资金流向 (Fund Flow)：
ETF 流量： 美国现货 ETF 周净流入/流出柱状图。
CME OI： CME 比特币期货未平仓合约变化（机构意愿）。
链上筹码 (Glassnode 独家)：
URPD (筹码分布)： 识别不同价格带的筹码堆积（寻找“最大痛点”）。
鲸鱼分群 (Cohort Analysis)： >10k BTC 钱包的颜色热力图（红色=派发，蓝色=吸筹）。
交易所余额： 币安/Coinbase 余额趋势。
衍生品与情绪：
清算热力图 (Liquidation Heatmap)： 识别高密度清算区（数据源：Coinglass）。
期权 Skew & PCR： 市场多空情绪偏离度。
数据源： Glassnode API (URPD, Cohort, Balance), Coinglass API (Liquidation, OI).
模块 3：ETH 深度分析 (ETH Deep Dive)
分析维度： 独立生态与汇率强弱。
数据指标：
汇率对： ETH/BTC 走势分析（山寨季信号）。
基本面： 基金会/财库地址持仓变动 (Glassnode/Etherscan)。
衍生品： ETH 期权 Skew 相对于 BTC 的溢价/折价。
数据源： Glassnode API, CCXT.
模块 4：行业要闻 (Key Narratives)
功能： 自动筛选并总结对基本面有实质影响的新闻。
实现： 抓取 CryptoPanic Top 50 新闻 -> 过滤关键词 (SEC, ETF, Hack) -> LLM 总结 Top 3 事件及其利空/利好属性。

三、 技术实施栈 (Tech Stack Recommendation)
后端语言： Python 3.9+
数据采集 (ETL)：
requests: 通用 API 调用。
glassnode-api-client: 官方封装库。
yfinance: 抓取美股数据。
pandas: 数据清洗与合并。
图表绘制 (Visualization)：
matplotlib 或 plotly: 关键。用于复刻 Glassnode 风格图表（自定义配色、字体、添加公司 Logo 水印）。
大模型集成 (LLM)：
OpenAI API (GPT-4o) 或 Anthropic API (Claude 3.5 Sonnet).
Prompt 策略： 使用 Few-Shot Learning，将过去 5 篇高质量人工周报作为样本喂给模型，让其模仿语调。

四、 自动化工作流 (Workflow)
周五收盘后 (Trigger)： 定时任务启动 generate_report.py。
数据获取： 脚本并发请求 Glassnode, Coinglass, Yahoo 接口，下载 JSON 数据。
图表生成： Python 本地生成 20+ 张高清 PNG 图表，存入 /images 文件夹。
文案生成： 将提取的关键数据点（如 "ETF 流入 5亿", "鲸鱼吸筹评分 0.8"）组装成 Prompt，发送给 LLM。
报告合成： 脚本将 LLM 返回的 Markdown 文本与对应图片拼接，转换成 PDF 草稿。
人工审核： 分析师收到邮件通知，微调个别观点，发布。

