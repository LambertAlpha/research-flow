"""
数据抓取模块:封装 Glassnode, Coinglass, Yahoo Finance 等数据源
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
from .utils import cache_api_call, robust_api_call, logger

# 加载环境变量
load_dotenv()

# API Keys
GLASSNODE_API_KEY = os.getenv("GLASSNODE_API_KEY")
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")


# ============= Glassnode API =============

@cache_api_call(cache_ttl_hours=12)
def fetch_glassnode_urpd(asset: str = "BTC", days: int = 30) -> Dict:
    """
    获取 URPD (Unrealized Profit/Loss Distribution) 筹码分布数据

    Args:
        asset: 资产符号, "BTC" 或 "ETH"
        days: 回溯天数

    Returns:
        {
            "timestamps": [timestamp1, timestamp2, ...],
            "prices": [price1, price2, ...],
            "supply": [supply1, supply2, ...]
        }
    """
    if not GLASSNODE_API_KEY:
        logger.error("GLASSNODE_API_KEY 未设置")
        raise ValueError("请在 .env 文件中配置 GLASSNODE_API_KEY")

    url = "https://api.glassnode.com/v1/metrics/distribution/balance_1pct_holders"

    # 计算时间范围
    since = int((datetime.now() - timedelta(days=days)).timestamp())

    params = {
        "a": asset,
        "api_key": GLASSNODE_API_KEY,
        "s": since,
        "i": "24h"  # 每日数据
    }

    try:
        data = robust_api_call(url, params=params)

        # 转换格式
        result = {
            "timestamps": [item["t"] for item in data],
            "dates": [datetime.fromtimestamp(item["t"]).strftime('%Y-%m-%d') for item in data],
            "values": [item["v"] for item in data]
        }

        logger.info(f"成功获取 {asset} URPD 数据, 共 {len(result['timestamps'])} 条记录")
        return result

    except Exception as e:
        logger.error(f"获取 URPD 数据失败: {e}")
        raise


@cache_api_call(cache_ttl_hours=12)
def fetch_glassnode_etf_flow(asset: str = "BTC", days: int = 30) -> Dict:
    """
    获取 ETF 资金流向数据

    Args:
        asset: 资产符号
        days: 回溯天数

    Returns:
        {
            "dates": [date1, date2, ...],
            "net_flow": [flow1, flow2, ...]
        }
    """
    if not GLASSNODE_API_KEY:
        raise ValueError("请在 .env 文件中配置 GLASSNODE_API_KEY")

    # Glassnode 的 ETF 流向指标
    url = "https://api.glassnode.com/v1/metrics/indicators/sopr"

    since = int((datetime.now() - timedelta(days=days)).timestamp())

    params = {
        "a": asset,
        "api_key": GLASSNODE_API_KEY,
        "s": since,
        "i": "24h"
    }

    try:
        data = robust_api_call(url, params=params)

        result = {
            "dates": [datetime.fromtimestamp(item["t"]).strftime('%Y-%m-%d') for item in data],
            "values": [item["v"] for item in data]
        }

        logger.info(f"成功获取 {asset} ETF Flow 数据, 共 {len(result['dates'])} 条记录")
        return result

    except Exception as e:
        logger.error(f"获取 ETF Flow 数据失败: {e}")
        raise


@cache_api_call(cache_ttl_hours=12)
def fetch_glassnode_whale_cohort(asset: str = "BTC", days: int = 90) -> Dict:
    """
    获取鲸鱼分群数据 (Whale Cohort Analysis)

    Args:
        asset: 资产符号
        days: 回溯天数

    Returns:
        {
            "dates": [date1, date2, ...],
            "whale_balance": [balance1, balance2, ...],
            "shark_balance": [balance1, balance2, ...]
        }
    """
    if not GLASSNODE_API_KEY:
        raise ValueError("请在 .env 文件中配置 GLASSNODE_API_KEY")

    # 鲸鱼地址 (>1000 BTC)
    url_whale = "https://api.glassnode.com/v1/metrics/distribution/balance_1k_10k"

    since = int((datetime.now() - timedelta(days=days)).timestamp())

    params = {
        "a": asset,
        "api_key": GLASSNODE_API_KEY,
        "s": since,
        "i": "24h"
    }

    try:
        whale_data = robust_api_call(url_whale, params=params)

        result = {
            "dates": [datetime.fromtimestamp(item["t"]).strftime('%Y-%m-%d') for item in whale_data],
            "whale_balance": [item["v"] for item in whale_data]
        }

        logger.info(f"成功获取 {asset} Whale Cohort 数据")
        return result

    except Exception as e:
        logger.error(f"获取 Whale Cohort 数据失败: {e}")
        raise


# ============= Yahoo Finance =============

@cache_api_call(cache_ttl_hours=12)
def fetch_yahoo_data(ticker: str, days: int = 30) -> Dict:
    """
    从 Yahoo Finance 获取宏观数据

    Args:
        ticker: 股票/指数代码, 如 "DX-Y.NYB" (美元指数), "^TNX" (10年期美债), "NVDA"
        days: 回溯天数

    Returns:
        {
            "dates": [date1, date2, ...],
            "close": [price1, price2, ...],
            "volume": [vol1, vol2, ...]
        }
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 使用 yfinance 获取数据
        data = yf.download(
            ticker,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            progress=False
        )

        if data.empty:
            logger.warning(f"未获取到 {ticker} 的数据")
            return {"dates": [], "close": [], "volume": []}

        result = {
            "dates": data.index.strftime('%Y-%m-%d').tolist(),
            "close": data['Close'].tolist(),
            "volume": data['Volume'].tolist() if 'Volume' in data.columns else []
        }

        logger.info(f"成功获取 {ticker} 数据, 共 {len(result['dates'])} 天")
        return result

    except Exception as e:
        logger.error(f"获取 Yahoo Finance 数据失败 ({ticker}): {e}")
        raise


# ============= Coinglass API (补充:清算数据等) =============

@cache_api_call(cache_ttl_hours=12)
def fetch_coinglass_liquidation(symbol: str = "BTC", days: int = 7) -> Dict:
    """
    获取清算数据 (Liquidation Heatmap)

    Args:
        symbol: 币种符号
        days: 回溯天数

    Returns:
        {
            "dates": [date1, date2, ...],
            "long_liquidation": [amount1, amount2, ...],
            "short_liquidation": [amount1, amount2, ...]
        }
    """
    if not COINGLASS_API_KEY:
        logger.warning("COINGLASS_API_KEY 未设置, 使用模拟数据")
        # 返回模拟数据用于开发
        return {
            "dates": [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)],
            "long_liquidation": [1000000 * (i+1) for i in range(days)],
            "short_liquidation": [800000 * (i+1) for i in range(days)]
        }

    # Coinglass API 端点 (实际使用时需要查阅官方文档)
    url = f"https://open-api.coinglass.com/public/v2/liquidation_history"

    params = {
        "symbol": symbol,
        "interval": "1d"
    }

    headers = {
        "coinglassSecret": COINGLASS_API_KEY
    }

    try:
        data = robust_api_call(url, params=params, headers=headers)

        # 实际数据处理逻辑需要根据 Coinglass API 响应格式调整
        logger.info(f"成功获取 {symbol} 清算数据")
        return data

    except Exception as e:
        logger.error(f"获取 Coinglass 清算数据失败: {e}")
        # 降级:返回空数据
        return {"dates": [], "long_liquidation": [], "short_liquidation": []}


# ============= 数据整合函数 =============

def fetch_module_data(module_name: str, config: Dict) -> Dict:
    """
    根据模块名称获取对应的数据

    Args:
        module_name: 模块名称 ('macro', 'btc', 'eth', 'news')
        config: 配置参数 {date_range: (start, end), ...}

    Returns:
        模块数据字典
    """
    days = 30  # 默认30天

    if module_name == "macro":
        # 宏观模块:美元指数、美债、美股、加密相关股票
        return {
            "dxy": fetch_yahoo_data("DX-Y.NYB", days=days),
            "us10y": fetch_yahoo_data("^TNX", days=days),
            "sp500": fetch_yahoo_data("^GSPC", days=days),
            "nvda": fetch_yahoo_data("NVDA", days=days),
            "coin": fetch_yahoo_data("COIN", days=days),
            "mstr": fetch_yahoo_data("MSTR", days=days)  # MicroStrategy
        }

    elif module_name == "btc":
        # BTC 深度分析
        return {
            "price": fetch_yahoo_data("BTC-USD", days=days),
            "urpd": fetch_glassnode_urpd("BTC", days=days),
            "etf_flow": fetch_glassnode_etf_flow("BTC", days=days),
            "whale_cohort": fetch_glassnode_whale_cohort("BTC", days=90),
            "liquidation": fetch_coinglass_liquidation("BTC", days=7)
        }

    elif module_name == "eth":
        # ETH 分析
        return {
            "price": fetch_yahoo_data("ETH-USD", days=days),
            "eth_btc_ratio": {
                "eth": fetch_yahoo_data("ETH-USD", days=days),
                "btc": fetch_yahoo_data("BTC-USD", days=days)
            }
        }

    elif module_name == "news":
        # 新闻模块 (暂时返回空数据,后续接入 CryptoPanic)
        return {
            "top_news": []
        }

    else:
        logger.error(f"未知的模块名称: {module_name}")
        return {}


if __name__ == "__main__":
    # 测试代码
    print("测试 Yahoo Finance 数据获取:")
    btc_data = fetch_yahoo_data("BTC-USD", days=7)
    print(f"BTC 最近7天数据: {len(btc_data['dates'])} 条记录")
    print(f"最新价格: ${btc_data['close'][-1]:.2f}")

    print("\n测试 Glassnode 数据获取 (需要有效的 API Key):")
    try:
        urpd_data = fetch_glassnode_urpd("BTC", days=7)
        print(f"URPD 数据: {len(urpd_data['dates'])} 条记录")
    except Exception as e:
        print(f"Glassnode 测试跳过: {e}")
