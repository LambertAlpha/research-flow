#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 检索测试脚本
演示如何使用 RAGManager 查询历史报告
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 强制重新加载环境变量
load_dotenv(project_root / ".env", override=True)

from modules.rag_manager import RAGManager

def test_basic_retrieval():
    """测试基础检索功能"""
    print("=" * 60)
    print("📚 RAG 检索测试")
    print("=" * 60)

    # 初始化 RAG Manager
    rag = RAGManager()

    # 获取向量库统计信息
    stats = rag.get_stats()
    print(f"\n📊 向量库信息:")
    print(f"   - 总文档数: {stats['total_chunks']}")
    print(f"   - Collection: {stats['collection_name']}")
    print(f"   - 存储路径: {stats['chroma_dir']}")

    # 测试 1: BTC 技术分析检索
    print("\n" + "=" * 60)
    print("🔍 测试 1: BTC 技术分析检索")
    print("=" * 60)

    current_btc_data = {
        "current_price": 98000,
        "ma7": 95000,  # 价格在 MA7 之上,上涨趋势
        "weekly_change": 5.2
    }

    context = rag.retrieve_context("btc_analysis", current_btc_data)

    print("\n📖 检索到的论证示例:")
    print(context["reasoning_examples"][:500] + "...\n")

    print("📖 完整参考片段预览:")
    print(context["style_guide"][:300] + "...\n")

    # 测试 2: 宏观分析检索
    print("=" * 60)
    print("🔍 测试 2: 宏观分析检索")
    print("=" * 60)

    current_macro_data = {
        "dxy": 103.5,
        "us10y": 4.2
    }

    macro_context = rag.retrieve_context("macro_analysis", current_macro_data)

    print("\n📖 宏观分析论证示例:")
    print(macro_context["reasoning_examples"][:500] + "...\n")

    # 测试 3: 直接查询向量数据库
    print("=" * 60)
    print("🔍 测试 3: 直接相似度搜索")
    print("=" * 60)

    results = rag.vector_store.similarity_search(
        "BTC 突破关键阻力位后的走势分析",
        k=3,
        filter={"$and": [{"section": "BTC Analysis"}, {"granularity": "fine"}]}
    )

    print(f"\n找到 {len(results)} 个相关文档:\n")
    for i, doc in enumerate(results, 1):
        print(f"📄 结果 {i}:")
        print(f"   日期: {doc.metadata.get('date')}")
        print(f"   类型: {doc.metadata.get('analysis_type')}")
        print(f"   内容: {doc.page_content[:100]}...")
        print()

if __name__ == "__main__":
    test_basic_retrieval()
