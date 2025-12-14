"""
Crypto 自动化投研周报系统 - Streamlit 主界面
"""

import streamlit as st
from datetime import datetime, timedelta
import os
from modules.data_fetcher import fetch_module_data, fetch_yahoo_data
from modules.chart_builder import generate_module_charts
from modules.utils import get_cache_info, clear_cache
from modules.llm_writer import LLMWriter, ContentCache, prepare_btc_context, prepare_macro_context
from modules.pdf_exporter import generate_report_pdf
from modules.agent_graph import run_report_generation, get_workflow_visualization

# 页面配置
st.set_page_config(
    page_title="Crypto 周报生成系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #34495e;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .cache-info {
        background-color: #ecf0f1;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 主标题
st.markdown('<div class="main-header">📊 Crypto 自动化投研周报系统</div>', unsafe_allow_html=True)

# ============= 侧边栏配置 =============

with st.sidebar:
    st.header("⚙️ 配置面板")

    # 日期范围选择
    st.subheader("📅 日期范围")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    date_range = st.date_input(
        "选择数据范围",
        value=(start_date, end_date),
        max_value=end_date
    )

    # 模块选择
    st.subheader("📂 报告模块")
    modules = {
        "macro": st.checkbox("宏观与相关资产", value=True),
        "btc": st.checkbox("BTC 深度分析", value=True),
        "eth": st.checkbox("ETH 分析", value=False),
        "news": st.checkbox("行业要闻", value=False)
    }

    selected_modules = [k for k, v in modules.items() if v]

    # 图表参数
    st.subheader("📈 图表参数")
    ma_periods = st.multiselect(
        "移动平均线周期",
        options=[10, 20, 50, 100, 200],
        default=[50, 200]
    )

    chart_dpi = st.select_slider(
        "图表分辨率 (DPI)",
        options=[150, 200, 250, 300, 350, 400],
        value=300
    )

    show_watermark = st.checkbox("显示水印", value=True)

    # 高级选项
    with st.expander("🔧 高级选项"):
        normalize_prices = st.checkbox("价格标准化 (加密股票图)", value=True, help="将所有价格标准化为第一天=100,便于对比")
        show_volume = st.checkbox("显示交易量", value=False, help="在价格图表中叠加交易量")
        data_source = st.selectbox(
            "数据源优先级",
            options=["Glassnode 优先", "Yahoo Finance 优先", "全部使用"],
            index=0
        )

    # 缓存管理
    st.subheader("💾 缓存管理")
    cache_info = get_cache_info()
    st.markdown(f"""
    <div class="cache-info">
        <strong>缓存统计:</strong><br>
        文件数量: {cache_info['count']}<br>
        总大小: {cache_info['total_size_mb']} MB<br>
        最早: {cache_info['oldest']}<br>
        最新: {cache_info['newest']}
    </div>
    """, unsafe_allow_html=True)

    if st.button("🗑️ 清除所有缓存"):
        clear_cache()
        st.success("缓存已清除")
        st.rerun()

    st.divider()

    # 系统信息
    st.caption(f"版本: v0.1.0 (MVP)")
    st.caption(f"更新: {datetime.now().strftime('%Y-%m-%d')}")


# ============= 主界面 =============

# 快速统计面板
st.markdown('<div class="section-header">📌 快速预览</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

# 获取 BTC 最新价格
try:
    btc_data = fetch_yahoo_data("BTC-USD", days=7)
    btc_price = btc_data['close'][-1]
    btc_change = ((btc_data['close'][-1] / btc_data['close'][0]) - 1) * 100

    with col1:
        st.metric(
            label="BTC 价格",
            value=f"${btc_price:,.0f}",
            delta=f"{btc_change:+.2f}% (7天)"
        )
except Exception as e:
    with col1:
        st.metric(label="BTC 价格", value="加载中...", delta="--")

# 占位符指标
with col2:
    st.metric(label="ETF 净流入", value="加载中...", delta="--")

with col3:
    st.metric(label="鲸鱼吸筹", value="加载中...", delta="--")

with col4:
    st.metric(label="缓存文件", value=cache_info['count'], delta="--")

st.divider()

# ============= 数据获取和图表生成 =============

st.markdown('<div class="section-header">📊 图表生成</div>', unsafe_allow_html=True)

if not selected_modules:
    st.warning("请在侧边栏至少选择一个报告模块")
else:
    if st.button("🚀 生成图表", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, module in enumerate(selected_modules):
            try:
                status_text.text(f"正在处理模块: {module.upper()}...")
                progress_bar.progress((idx + 1) / len(selected_modules))

                # 获取数据
                with st.spinner(f"正在获取 {module} 模块数据..."):
                    data = fetch_module_data(module, {})

                # 生成图表
                with st.spinner(f"正在生成 {module} 模块图表..."):
                    chart_paths = generate_module_charts(module, data)

                # 显示图表
                if chart_paths:
                    st.markdown(f'<div class="section-header">{module.upper()} 模块图表</div>', unsafe_allow_html=True)

                    # 根据图表数量动态调整布局
                    if len(chart_paths) == 1:
                        st.image(chart_paths[0], use_container_width=True)
                        # 添加下载按钮
                        with open(chart_paths[0], "rb") as f:
                            st.download_button(
                                label="📥 下载图表",
                                data=f,
                                file_name=os.path.basename(chart_paths[0]),
                                mime="image/png"
                            )

                    elif len(chart_paths) == 2:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(chart_paths[0], use_container_width=True)
                            with open(chart_paths[0], "rb") as f:
                                st.download_button(
                                    label="📥 下载",
                                    data=f,
                                    file_name=os.path.basename(chart_paths[0]),
                                    mime="image/png",
                                    key=f"download_{chart_paths[0]}"
                                )
                        with col2:
                            st.image(chart_paths[1], use_container_width=True)
                            with open(chart_paths[1], "rb") as f:
                                st.download_button(
                                    label="📥 下载",
                                    data=f,
                                    file_name=os.path.basename(chart_paths[1]),
                                    mime="image/png",
                                    key=f"download_{chart_paths[1]}"
                                )

                    else:
                        # 多张图表:使用 expander 折叠显示
                        for idx, chart_path in enumerate(chart_paths, 1):
                            with st.expander(f"图表 {idx}: {os.path.basename(chart_path)}", expanded=(idx<=2)):
                                st.image(chart_path, use_container_width=True)
                                with open(chart_path, "rb") as f:
                                    st.download_button(
                                        label="📥 下载此图表",
                                        data=f,
                                        file_name=os.path.basename(chart_path),
                                        mime="image/png",
                                        key=f"download_{idx}_{chart_path}"
                                    )

                    st.success(f"✅ {module.upper()} 模块完成 ({len(chart_paths)} 张图表)")
                else:
                    st.warning(f"⚠️ {module.upper()} 模块暂无图表")

            except Exception as e:
                st.error(f"❌ {module.upper()} 模块处理失败: {str(e)}")

        progress_bar.progress(1.0)
        status_text.text("所有模块处理完成!")
        st.balloons()

# ============= LLM 文案生成 =============

st.divider()
st.markdown('<div class="section-header">✍️ LLM 文案生成</div>', unsafe_allow_html=True)

# LLM 配置
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    llm_model = st.selectbox(
        "选择 LLM 模型",
        options=["gpt-4o", "gpt-4o-mini", "gemini-pro"],
        help="GPT-4o 质量更高但成本更高，GPT-4o-mini 性价比高，Gemini 免费"
    )

with col2:
    llm_temperature = st.slider(
        "生成温度",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="较低温度生成更保守，较高温度更具创造性"
    )

with col3:
    enable_llm = st.checkbox("启用 LLM", value=False)

if enable_llm:
    # 检查 API Key
    api_key_available = False
    if llm_model.startswith("gpt"):
        api_key_available = os.getenv("OPENAI_API_KEY") is not None
    elif llm_model.startswith("gemini"):
        api_key_available = os.getenv("GEMINI_API_KEY") is not None

    if not api_key_available:
        st.error(f"⚠️ 未检测到 {llm_model.upper()} API Key，请在 .env 文件中配置")
    else:
        if st.button("🤖 生成文案", type="primary", use_container_width=True):
            try:
                with st.spinner("正在生成文案..."):
                    # 初始化 LLM Writer
                    writer = LLMWriter(model=llm_model)

                    # 获取数据
                    btc_data = fetch_yahoo_data("BTC-USD", days=30)
                    macro_data_raw = fetch_module_data("macro", {})

                    # 准备上下文
                    btc_context = prepare_btc_context(btc_data)
                    macro_context = prepare_macro_context(macro_data_raw)

                    # 生成文案
                    tasks = [
                        {"type": "btc_analysis", "context": btc_context},
                        {"type": "macro_analysis", "context": macro_context}
                    ]

                    results = writer.generate_batch(tasks)

                    # 保存到缓存
                    cache = ContentCache()
                    cache_path = cache.save(results)

                    # 显示结果
                    st.success(f"✅ 文案生成完成！已保存到: {cache_path}")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("### 📈 BTC 市场分析")
                        st.markdown(results.get("btc_analysis", "生成失败"))

                    with col2:
                        st.markdown("### 🌍 宏观环境分析")
                        st.markdown(results.get("macro_analysis", "生成失败"))

                    # 下载按钮
                    import json
                    content_json = json.dumps(results, ensure_ascii=False, indent=2)
                    st.download_button(
                        label="📥 下载文案 (JSON)",
                        data=content_json,
                        file_name=f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )

            except Exception as e:
                st.error(f"❌ 文案生成失败: {str(e)}")
                import traceback
                with st.expander("查看错误详情"):
                    st.code(traceback.format_exc())

        # 历史版本管理
        with st.expander("📚 历史文案版本"):
            cache = ContentCache()
            versions = cache.list_versions()

            if not versions:
                st.info("暂无历史版本")
            else:
                for v in versions[:5]:  # 只显示最近 5 个版本
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"版本: {v['version']} ({v['timestamp']})")
                    with col2:
                        if st.button("加载", key=f"load_{v['version']}"):
                            loaded = cache.load(v['version'])
                            st.json(loaded['content'])

# ============= 数据表格预览 (可选) =============

with st.expander("📋 查看原始数据"):
    st.markdown("### BTC 价格数据 (最近7天)")

    try:
        btc_data = fetch_yahoo_data("BTC-USD", days=7)
        import pandas as pd
        df = pd.DataFrame({
            "日期": btc_data['dates'],
            "收盘价": btc_data['close'],
            "交易量": btc_data['volume']
        })
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"无法加载数据: {e}")

# ============= PDF 导出 =============

st.divider()
st.markdown('<div class="section-header">📄 PDF 导出</div>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col1:
    st.info("生成专业的 PDF 周报，包含所有图表和文案")

with col2:
    enable_pdf = st.checkbox("启用 PDF", value=False)

if enable_pdf:
    if st.button("📥 生成 PDF 报告", type="primary", use_container_width=True):
        try:
            with st.spinner("正在生成 PDF..."):
                # 准备数据
                chart_paths = {"macro": []}
                content = {}

                # 获取图表路径
                import glob
                macro_charts = glob.glob("output/images/*/macro_*.png")
                if macro_charts:
                    chart_paths["macro"] = sorted(macro_charts, reverse=True)[:2]

                # 获取文案
                cache = ContentCache()
                versions = cache.list_versions()
                if versions:
                    latest = cache.load(versions[0]["version"])
                    content = latest.get("content", {})

                # 准备指标
                btc_data = fetch_yahoo_data("BTC-USD", days=7)
                btc_price = btc_data["close"][-1]
                btc_change = ((btc_data["close"][-1] - btc_data["close"][-7]) / btc_data["close"][-7] * 100) if len(btc_data["close"]) >= 7 else 0

                metrics = [
                    {"label": "BTC 价格", "value": f"${btc_price:,.0f}", "delta": f"{btc_change:+.2f}%"},
                    {"label": "报告模块", "value": str(len(chart_paths)), "delta": "--"},
                    {"label": "图表数量", "value": str(sum(len(c) for c in chart_paths.values())), "delta": "--"}
                ]

                # 生成 PDF
                pdf_path = generate_report_pdf(
                    chart_paths=chart_paths,
                    content=content,
                    metrics=metrics
                )

                st.success(f"✅ PDF 已生成: {pdf_path}")

                # 下载按钮
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 下载 PDF",
                        data=f,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf"
                    )

        except Exception as e:
            st.error(f"❌ PDF 生成失败: {str(e)}")
            with st.expander("查看错误详情"):
                import traceback
                st.code(traceback.format_exc())

# ============= Multi-Agent 工作流 =============

st.divider()
st.markdown('<div class="section-header">🤖 Multi-Agent 自动化工作流</div>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col1:
    st.info("使用 LangGraph Multi-Agent 系统自动化完成数据抓取→图表生成→文案撰写→质量审核")

with col2:
    enable_agent = st.checkbox("启用 Agent", value=False)

if enable_agent:
    # 显示工作流可视化
    with st.expander("📊 查看工作流结构"):
        st.markdown("```mermaid\n" + get_workflow_visualization() + "\n```")
        st.caption("工作流包含 5 个 Agent: Chief Editor, Data Engineer, Chartist, Senior Analyst, Debate Node")

    if st.button("🚀 启动 Multi-Agent 工作流", type="primary", use_container_width=True):
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()

            # 确定报告周期
            today = datetime.now()
            week_start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            week_end = today.strftime("%Y-%m-%d")
            report_period = f"{week_start} ~ {week_end}"

            status_text.text(f"正在启动工作流... 报告周期: {report_period}")
            progress_bar.progress(0.1)

            # 运行工作流
            final_state = run_report_generation(report_period, verbose=False)

            progress_bar.progress(1.0)
            status_text.text("工作流执行完成!")

            # 显示结果
            st.success("✅ Multi-Agent 工作流执行成功！")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("质量评分", f"{final_state.get('quality_score', 0):.1f}/100")
            with col2:
                st.metric("辩论轮数", final_state.get("debate_rounds", 0))
            with col3:
                chart_count = sum(len(charts) for charts in final_state.get("chart_paths", {}).values())
                st.metric("生成图表", chart_count)

            # 显示生成的文案
            if final_state.get("final_content"):
                st.markdown("### 📝 生成的文案")
                for key, text in final_state["final_content"].items():
                    with st.expander(f"{key}", expanded=True):
                        st.markdown(text)

            # 显示问题（如果有）
            if final_state.get("issues"):
                st.warning("⚠️ 检测到的问题:")
                for issue in final_state["issues"]:
                    st.text(f"• {issue}")

        except Exception as e:
            st.error(f"❌ 工作流执行失败: {str(e)}")
            with st.expander("查看错误详情"):
                import traceback
                st.code(traceback.format_exc())

# ============= 页脚 =============

st.divider()
st.markdown("""
<div style="text-align: center; color: #7f8c8d; padding: 2rem;">
    <p>Crypto 自动化投研周报系统 v0.2.0 (Beta)</p>
    <p>数据来源: Glassnode, Yahoo Finance, Coinglass</p>
    <p>⚠️ 注意: 确保已在 .env 文件中配置 API Keys</p>
</div>
""", unsafe_allow_html=True)
