#!/usr/bin/env python3
"""
快速测试数据抓取功能
"""

import sys
from modules.data_fetcher import fetch_yahoo_data

print("=" * 60)
print("测试 Yahoo Finance 数据抓取...")
print("=" * 60)

try:
    print("\n1. 测试 BTC 数据获取 (7天)...")
    btc_data = fetch_yahoo_data("BTC-USD", days=7)
    print(f"   ✅ 成功获取 {len(btc_data['dates'])} 条记录")
    print(f"   最新日期: {btc_data['dates'][-1]}")
    print(f"   最新价格: ${btc_data['close'][-1]:,.2f}")

    print("\n2. 测试 DXY 美元指数数据...")
    dxy_data = fetch_yahoo_data("DX-Y.NYB", days=7)
    print(f"   ✅ 成功获取 {len(dxy_data['dates'])} 条记录")

    print("\n3. 测试 NVDA 股票数据...")
    nvda_data = fetch_yahoo_data("NVDA", days=7)
    print(f"   ✅ 成功获取 {len(nvda_data['dates'])} 条记录")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过!")
    print("=" * 60)
    sys.exit(0)

except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
