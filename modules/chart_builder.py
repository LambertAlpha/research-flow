"""
图表生成工厂:生成专业的加密货币分析图表
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from .utils import logger

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

# 加载全局样式
STYLE_PATH = os.path.join(PROJECT_ROOT, "assets/style.mplstyle")
if os.path.exists(STYLE_PATH):
    plt.style.use(STYLE_PATH)
    logger.info(f"已加载 Matplotlib 样式: {STYLE_PATH}")
else:
    logger.warning(f"未找到样式文件: {STYLE_PATH}, 使用默认样式")

# Logo 路径
LOGO_PATH = os.path.join(PROJECT_ROOT, "assets/logo.png")

# 输出目录
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output/images")


def add_watermark(fig, logo_path: str = LOGO_PATH, alpha: float = 0.15):
    """
    在图表右下角添加透明水印

    Args:
        fig: Matplotlib Figure 对象
        logo_path: Logo 文件路径
        alpha: 透明度 (0-1)
    """
    if not os.path.exists(logo_path):
        logger.warning(f"Logo 文件不存在: {logo_path}, 跳过水印")
        return

    try:
        logo = mpimg.imread(logo_path)
        # 在右下角添加 Logo
        ax_logo = fig.add_axes([0.80, 0.02, 0.15, 0.15], anchor='SE', zorder=1)
        ax_logo.imshow(logo, alpha=alpha)
        ax_logo.axis('off')
        logger.debug("水印添加成功")
    except Exception as e:
        logger.warning(f"添加水印失败: {e}")


def save_chart(fig, filename: str, dpi: int = 300) -> str:
    """
    保存图表为高清 PNG

    Args:
        fig: Matplotlib Figure 对象
        filename: 文件名
        dpi: 分辨率

    Returns:
        保存的文件路径
    """
    # 按日期创建子目录
    date_dir = os.path.join(OUTPUT_DIR, datetime.now().strftime('%Y-%m-%d'))
    os.makedirs(date_dir, exist_ok=True)

    filepath = os.path.join(date_dir, filename)

    fig.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    logger.info(f"图表已保存: {filepath}")
    return filepath


# ============= 图表生成函数 =============

def generate_btc_price_chart(data: Dict, ma_periods: List[int] = [50, 200]) -> str:
    """
    生成 BTC 价格走势图 + 均线

    Args:
        data: {"dates": [...], "close": [...]}
        ma_periods: 均线周期列表

    Returns:
        图表文件路径
    """
    fig, ax = plt.subplots(figsize=(12, 7))

    dates = data['dates']
    prices = data['close']

    # 绘制价格曲线
    ax.plot(dates, prices, label='BTC Price', linewidth=2.5, color='#3498db')

    # 计算并绘制均线
    import pandas as pd
    df = pd.DataFrame({"price": prices})

    for period in ma_periods:
        ma = df['price'].rolling(window=period).mean()
        ax.plot(dates, ma, label=f'MA{period}', linewidth=2, alpha=0.7)

    ax.set_xlabel('Date')
    ax.set_ylabel('Price (USD)')
    ax.set_title('Bitcoin Price Chart with Moving Averages')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 旋转 x 轴标签
    plt.xticks(rotation=45, ha='right')

    # 添加水印
    add_watermark(fig)

    return save_chart(fig, 'btc_price.png')


def generate_urpd_chart(data: Dict) -> str:
    """
    生成 URPD (筹码分布) 柱状图

    Args:
        data: {"dates": [...], "values": [...]}

    Returns:
        图表文件路径
    """
    fig, ax = plt.subplots(figsize=(12, 7))

    dates = data['dates'][-30:]  # 最近30天
    values = data['values'][-30:]

    # 绘制柱状图
    bars = ax.bar(dates, values, color='#3498db', alpha=0.7, edgecolor='none')

    # 高亮最高值
    max_idx = values.index(max(values))
    bars[max_idx].set_color('#e74c3c')

    ax.set_xlabel('Date')
    ax.set_ylabel('Supply Distribution')
    ax.set_title('Bitcoin URPD - Unrealized Profit/Loss Distribution')
    ax.grid(True, alpha=0.3, axis='y')

    plt.xticks(rotation=45, ha='right')

    # 添加水印
    add_watermark(fig)

    return save_chart(fig, 'btc_urpd.png')


def generate_etf_flow_chart(data: Dict) -> str:
    """
    生成 ETF 资金流向柱状图

    Args:
        data: {"dates": [...], "values": [...]}

    Returns:
        图表文件路径
    """
    fig, ax = plt.subplots(figsize=(12, 7))

    dates = data['dates'][-30:]
    values = data['values'][-30:]

    # 根据正负值使用不同颜色
    colors = ['#2ecc71' if v > 0 else '#e74c3c' for v in values]

    ax.bar(dates, values, color=colors, alpha=0.7, edgecolor='none')

    ax.set_xlabel('Date')
    ax.set_ylabel('Net Flow (BTC)')
    ax.set_title('Bitcoin ETF Daily Net Flow')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.grid(True, alpha=0.3, axis='y')

    plt.xticks(rotation=45, ha='right')

    add_watermark(fig)

    return save_chart(fig, 'btc_etf_flow.png')


def generate_crypto_stocks_chart(data: Dict) -> str:
    """
    生成加密相关股票对比图 (NVDA, COIN, MSTR)

    Args:
        data: {
            "nvda": {"dates": [...], "close": [...]},
            "coin": {"dates": [...], "close": [...]},
            "mstr": {"dates": [...], "close": [...]} (可选)
        }

    Returns:
        图表文件路径
    """
    import pandas as pd

    fig, ax = plt.subplots(figsize=(12, 7))

    # 标准化价格 (以第一天为基准 = 100)
    stocks = ['nvda', 'coin', 'mstr']
    colors = ['#2ecc71', '#e74c3c', '#f39c12']
    labels = ['NVIDIA (NVDA)', 'Coinbase (COIN)', 'MicroStrategy (MSTR)']

    for stock, color, label in zip(stocks, colors, labels):
        if stock in data and data[stock]['dates']:
            dates = data[stock]['dates']
            prices = data[stock]['close']

            # 标准化为百分比变化 (第一天 = 100)
            normalized = [(p / prices[0]) * 100 for p in prices]

            ax.plot(dates, normalized, label=label, linewidth=2.5, color=color)

    ax.axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_xlabel('Date')
    ax.set_ylabel('Normalized Price (First Day = 100)')
    ax.set_title('Crypto-Related Stocks Performance Comparison')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45, ha='right')

    add_watermark(fig)

    return save_chart(fig, 'crypto_stocks.png')


def generate_macro_overview_chart(data: Dict) -> str:
    """
    生成宏观指标总览图 (四合一子图)

    Args:
        data: {
            "dxy": {"dates": [...], "close": [...]},
            "us10y": {"dates": [...], "close": [...]},
            "sp500": {"dates": [...], "close": [...]},
            "nvda": {"dates": [...], "close": [...]}
        }

    Returns:
        图表文件路径
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Macro Overview: Key Indicators', fontsize=16, fontweight='bold')

    indicators = [
        ("dxy", "US Dollar Index (DXY)", axes[0, 0]),
        ("us10y", "10-Year Treasury Yield", axes[0, 1]),
        ("sp500", "S&P 500 Index", axes[1, 0]),
        ("nvda", "NVIDIA Stock Price", axes[1, 1])
    ]

    for key, title, ax in indicators:
        if key in data and data[key]['dates']:
            ax.plot(data[key]['dates'], data[key]['close'], linewidth=2, color='#3498db')
            ax.set_title(title)
            ax.set_xlabel('Date')
            ax.set_ylabel('Value')
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()

    add_watermark(fig)

    return save_chart(fig, 'macro_overview.png')


def generate_whale_cohort_heatmap(data: Dict) -> str:
    """
    生成鲸鱼分群热力图 (不同地址余额区间的持仓变化)

    Args:
        data: {"dates": [...], "whale_balance": [...]}

    Returns:
        图表文件路径
    """
    import pandas as pd

    fig, ax = plt.subplots(figsize=(12, 7))

    dates = data['dates']
    whale_balance = data['whale_balance']

    # 计算变化率
    df = pd.DataFrame({"balance": whale_balance})
    change = df['balance'].pct_change() * 100  # 转换为百分比

    # 绘制面积图
    ax.fill_between(range(len(dates)), 0, whale_balance, alpha=0.6, color='#3498db', label='Whale Balance (1k-10k BTC)')
    ax.plot(dates, whale_balance, linewidth=2, color='#2980b9')

    ax.set_xlabel('Date')
    ax.set_ylabel('Balance (BTC)')
    ax.set_title('Bitcoin Whale Cohort Analysis (1,000 - 10,000 BTC)')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, axis='y')

    plt.xticks(rotation=45, ha='right')

    add_watermark(fig)

    return save_chart(fig, 'btc_whale_cohort.png')


def generate_liquidation_heatmap(data: Dict) -> str:
    """
    生成清算热力图

    Args:
        data: {
            "dates": [...],
            "long_liquidation": [...],
            "short_liquidation": [...]
        }

    Returns:
        图表文件路径
    """
    fig, ax = plt.subplots(figsize=(12, 7))

    dates = data['dates']
    long_liq = data['long_liquidation']
    short_liq = data['short_liquidation']

    # 堆叠柱状图
    width = 0.8
    x = range(len(dates))

    ax.bar(x, long_liq, width, label='Long Liquidation', color='#e74c3c', alpha=0.7)
    ax.bar(x, short_liq, width, bottom=long_liq, label='Short Liquidation', color='#2ecc71', alpha=0.7)

    ax.set_xlabel('Date')
    ax.set_ylabel('Liquidation Amount (USD)')
    ax.set_title('Bitcoin Liquidation Heatmap (Long vs Short)')
    ax.set_xticks(x[::2])  # 每隔一个显示日期标签
    ax.set_xticklabels([dates[i] for i in x[::2]], rotation=45, ha='right')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, axis='y')

    add_watermark(fig)

    return save_chart(fig, 'btc_liquidation.png')


def generate_eth_btc_ratio_chart(data: Dict) -> str:
    """
    生成 ETH/BTC 汇率走势图

    Args:
        data: {
            "eth": {"dates": [...], "close": [...]},
            "btc": {"dates": [...], "close": [...]}
        }

    Returns:
        图表文件路径
    """
    fig, ax = plt.subplots(figsize=(12, 7))

    # 计算 ETH/BTC 比率
    import pandas as pd
    eth_prices = pd.Series(data['eth']['close'])
    btc_prices = pd.Series(data['btc']['close'])
    ratio = eth_prices / btc_prices

    dates = data['eth']['dates']

    ax.plot(dates, ratio, linewidth=2.5, color='#9b59b6')
    ax.set_xlabel('Date')
    ax.set_ylabel('ETH/BTC Ratio')
    ax.set_title('Ethereum vs Bitcoin Price Ratio')
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45, ha='right')

    add_watermark(fig)

    return save_chart(fig, 'eth_btc_ratio.png')


def generate_eth_foundation_balance(data: Dict) -> str:
    """
    生成以太坊基金会持仓变化图

    Args:
        data: {"dates": [...], "balance": [...]}

    Returns:
        图表文件路径
    """
    fig, ax = plt.subplots(figsize=(12, 7))

    dates = data.get('dates', [])
    balance = data.get('balance', [])

    if not dates or not balance:
        # 如果没有数据,使用模拟数据
        logger.warning("以太坊基金会数据暂无,使用模拟数据")
        from datetime import datetime, timedelta
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
        balance = [300000 - i*100 for i in range(30)]

    ax.plot(dates, balance, linewidth=2.5, color='#9b59b6', marker='o', markersize=4)
    ax.fill_between(range(len(dates)), 0, balance, alpha=0.2, color='#9b59b6')

    ax.set_xlabel('Date')
    ax.set_ylabel('ETH Balance')
    ax.set_title('Ethereum Foundation Holdings')
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45, ha='right')

    add_watermark(fig)

    return save_chart(fig, 'eth_foundation.png')


# ============= 模块图表生成入口 =============

def generate_module_charts(module_name: str, data: Dict) -> List[str]:
    """
    根据模块名称生成对应的所有图表

    Args:
        module_name: 模块名称
        data: 模块数据

    Returns:
        生成的图表文件路径列表
    """
    chart_paths = []

    try:
        if module_name == "btc":
            # BTC 价格图
            if 'price' in data:
                chart_paths.append(generate_btc_price_chart(data['price']))

            # URPD 筹码分布
            if 'urpd' in data:
                chart_paths.append(generate_urpd_chart(data['urpd']))

            # ETF 资金流向
            if 'etf_flow' in data:
                chart_paths.append(generate_etf_flow_chart(data['etf_flow']))

            # 鲸鱼分群
            if 'whale_cohort' in data:
                chart_paths.append(generate_whale_cohort_heatmap(data['whale_cohort']))

            # 清算热力图
            if 'liquidation' in data:
                chart_paths.append(generate_liquidation_heatmap(data['liquidation']))

        elif module_name == "macro":
            # 宏观总览图 (四合一)
            chart_paths.append(generate_macro_overview_chart(data))

            # 加密相关股票对比
            if 'nvda' in data or 'coin' in data:
                chart_paths.append(generate_crypto_stocks_chart(data))

        elif module_name == "eth":
            # ETH/BTC 汇率
            if 'eth_btc_ratio' in data:
                chart_paths.append(generate_eth_btc_ratio_chart(data['eth_btc_ratio']))

            # 以太坊基金会持仓
            if 'foundation_balance' in data:
                chart_paths.append(generate_eth_foundation_balance(data['foundation_balance']))

        logger.info(f"成功生成 {module_name} 模块的 {len(chart_paths)} 张图表")

    except Exception as e:
        logger.error(f"生成 {module_name} 模块图表失败: {e}")

    return chart_paths


if __name__ == "__main__":
    # 测试代码
    print("图表生成模块测试")
    test_data = {
        "dates": ["2025-12-01", "2025-12-02", "2025-12-03"],
        "close": [40000, 41000, 42000]
    }

    try:
        path = generate_btc_price_chart(test_data)
        print(f"测试图表已生成: {path}")
    except Exception as e:
        print(f"测试失败: {e}")
