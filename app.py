"""
Crypto 自动化投研周报系统 - Streamlit 主界面
"""

import streamlit as st
from datetime import datetime, timedelta
import os
from modules.data_fetcher import fetch_module_data, fetch_yahoo_data
from modules.chart_builder import generate_module_charts
from modules.utils import get_cache_info, clear_cache

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
                    elif len(chart_paths) == 2:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(chart_paths[0], use_container_width=True)
                        with col2:
                            st.image(chart_paths[1], use_container_width=True)
                    else:
                        for chart_path in chart_paths:
                            st.image(chart_path, use_container_width=True)

                    st.success(f"✅ {module.upper()} 模块完成 ({len(chart_paths)} 张图表)")
                else:
                    st.warning(f"⚠️ {module.upper()} 模块暂无图表")

            except Exception as e:
                st.error(f"❌ {module.upper()} 模块处理失败: {str(e)}")

        progress_bar.progress(1.0)
        status_text.text("所有模块处理完成!")
        st.balloons()

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

# ============= 页脚 =============

st.divider()
st.markdown("""
<div style="text-align: center; color: #7f8c8d; padding: 2rem;">
    <p>Crypto 自动化投研周报系统 v0.1.0 (MVP)</p>
    <p>数据来源: Glassnode, Yahoo Finance, Coinglass</p>
    <p>⚠️ 注意: 确保已在 .env 文件中配置 API Keys</p>
</div>
""", unsafe_allow_html=True)
