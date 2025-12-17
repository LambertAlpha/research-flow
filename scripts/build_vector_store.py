#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build RAG Vector Store Script
Process historical weekly reports from raw_weekly_report_data and store into ChromaDB
"""

import os
import sys
import logging
import re
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Force reload .env file
load_dotenv(project_root / ".env", override=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ========== Configuration ==========

PDF_DIR = project_root / "raw_weekly_report_data"
CHROMA_DIR = project_root / "chroma_db"
COLLECTION_NAME = "crypto_weekly_reports"

# Chinese-optimized separators (priority order)
CHINESE_SEPARATORS = [
    "\n\n",      # Paragraph breaks
    "。\n",      # Chinese period + newline
    "。",        # Chinese period
    "!",         # Exclamation
    "?",         # Question mark  
    "；",        # Chinese semicolon
    ",",         # Comma
    " ",         # Space
    ""           # Character-level fallback
]


# ========== PDF Parsing ==========

def extract_pdf_text(pdf_path: Path) -> List[Dict]:
    """
    Extract text from PDF with metadata
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of dicts with text and metadata
    """
    try:
        reader = PdfReader(pdf_path)
        
        # Extract date from filename (format: 2025-11-17.pdf)
        date = pdf_path.stem
        
        chunks = []
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            
            if not text or len(text.strip()) < 50:
                continue
                
            chunks.append({
                "text": text,
                "page": page_num,
                "date": date,
                "filename": pdf_path.name
            })
        
        logger.info(f"✅ {pdf_path.name}: Extracted {len(chunks)} pages")
        return chunks
        
    except Exception as e:
        logger.error(f"❌ {pdf_path.name} failed: {e}")
        return []


def classify_section_and_type(text: str) -> Dict[str, str]:
    """
    Classify section and analysis type based on keywords
    
    Args:
        text: Text content
        
    Returns:
        Dict with section and analysis_type
    """
    section = "Unclassified"
    analysis_type = "Other"
    
    # Identify section
    if any(kw in text for kw in ["美元指数", "美债", "DXY", "US10Y", "标普500", "Nasdaq", "纳指"]):
        section = "Macro"
        if any(kw in text for kw in ["NVDA", "COIN", "MSTR", "Coinbase", "Robinhood", "Strategy"]):
            analysis_type = "Related Assets"
        else:
            analysis_type = "Macro Environment"
    
    elif "BTC" in text or "比特币" in text or "bitcoin" in text.lower():
        section = "BTC Analysis"
        
        # Identify analysis type
        if any(kw in text for kw in ["均线", "MA", "阻力", "支撑", "K线", "MACD", "RSI", "技术"]):
            analysis_type = "Technical Analysis"
        elif any(kw in text for kw in ["ETF", "资金流", "净流入", "净流出", "Spot ETF", "资金"]):
            analysis_type = "Capital Flow"
        elif any(kw in text for kw in ["URPD", "链上", "鲸鱼", "地址", "Glassnode", "交易所"]):
            analysis_type = "On-Chain Data"
        elif any(kw in text for kw in ["期货", "期权", "未平仓", "资金费率", "OI", "衍生品"]):
            analysis_type = "Derivatives"
        elif any(kw in text for kw in ["因此,我们认为", "总结", "后市", "综上"]):
            analysis_type = "Summary"
    
    elif "ETH" in text or "以太坊" in text or "ethereum" in text.lower():
        section = "ETH Analysis"
        if any(kw in text for kw in ["资金", "ETF"]):
            analysis_type = "Capital Flow"
        else:
            analysis_type = "Technical Analysis"
    
    return {"section": section, "analysis_type": analysis_type}


def has_data_points(text: str) -> bool:
    """Check if text contains data points (numbers with units)"""
    pattern = r'[\$¥€][\d,]+|[\d.]+%|[\d.]+[KMB]'
    return bool(re.search(pattern, text))


def is_conclusion(text: str) -> bool:
    """Check if text is a conclusion paragraph"""
    conclusion_keywords = ["因此,我们认为", "因此,我們認為", "综上", "總結", "后市大概率", "我们预计", "我們預計"]
    return any(kw in text for kw in conclusion_keywords)


# ========== Vectorization ==========

def build_vector_store():
    """Build the vector store"""
    
    logger.info("=" * 60)
    logger.info("🚀 Starting RAG Vector Store Build")
    logger.info("=" * 60)
    
    # 1. Collect all PDFs
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    logger.info(f"📂 Found {len(pdf_files)} PDF files")
    
    if not pdf_files:
        logger.error(f"❌ No PDF files found in: {PDF_DIR}")
        return
    
    # 2. Parse PDFs
    all_raw_chunks = []
    logger.info("📄 Parsing PDF files...")
    for pdf_path in tqdm(pdf_files, desc="Parsing PDFs"):
        chunks = extract_pdf_text(pdf_path)
        all_raw_chunks.extend(chunks)
    
    logger.info(f"✅ Extracted {len(all_raw_chunks)} raw pages")
    
    # 3. Chunk into fine and coarse granularities
    logger.info("✂️  Chunking text...")
    
    # Fine-grained chunker (for specific techniques)
    fine_splitter = RecursiveCharacterTextSplitter(
        separators=CHINESE_SEPARATORS,
        chunk_size=300,
        chunk_overlap=100,
        length_function=len,
    )
    
    # Coarse-grained chunker (for full context)
    coarse_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "。\n", "##", "#"],
        chunk_size=600,
        chunk_overlap=150,
        length_function=len,
    )
    
    all_documents = []
    
    for raw_chunk in tqdm(all_raw_chunks, desc="Chunking with metadata"):
        text = raw_chunk["text"]
        base_metadata = {
            "date": raw_chunk["date"],
            "year_month": raw_chunk["date"][:7],
            "page": raw_chunk["page"],
            "filename": raw_chunk["filename"],
        }
        
        # Classify section and type
        classification = classify_section_and_type(text)
        base_metadata.update(classification)
        
        # Fine-grained chunks
        fine_chunks = fine_splitter.split_text(text)
        for chunk in fine_chunks:
            metadata = base_metadata.copy()
            metadata["granularity"] = "fine"
            metadata["word_count"] = len(chunk)
            metadata["has_data"] = has_data_points(chunk)
            metadata["is_conclusion"] = is_conclusion(chunk)
            
            all_documents.append(Document(
                page_content=chunk,
                metadata=metadata
            ))
        
        # Coarse-grained chunks
        coarse_chunks = coarse_splitter.split_text(text)
        for chunk in coarse_chunks:
            metadata = base_metadata.copy()
            metadata["granularity"] = "coarse"
            metadata["word_count"] = len(chunk)
            metadata["has_data"] = has_data_points(chunk)
            metadata["is_conclusion"] = is_conclusion(chunk)
            
            all_documents.append(Document(
                page_content=chunk,
                metadata=metadata
            ))
    
    logger.info(f"✅ Generated {len(all_documents)} document chunks")
    
    # 4. Vectorize and store
    logger.info("🔮 Vectorizing with OpenAI text-embedding-3-small...")
    logger.info("⚠️  This may take several minutes...")

    # Use EMBEDDING env var if available, otherwise fall back to OPENAI_API_KEY
    embedding_api_key = os.getenv("EMBEDDING") or os.getenv("EMBEDDINGS") or os.getenv("OPENAI_API_KEY")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=embedding_api_key)
    
    # Remove old vector store if exists
    if CHROMA_DIR.exists():
        logger.warning(f"⚠️  Removing old vector store: {CHROMA_DIR}")
        import shutil
        shutil.rmtree(CHROMA_DIR)
    
    # Batch add to avoid oversized requests
    batch_size = 100
    vector_store = None
    
    for i in tqdm(range(0, len(all_documents), batch_size), desc="Vectorizing"):
        batch = all_documents[i:i+batch_size]
        
        if vector_store is None:
            # First batch - create store
            vector_store = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                collection_name=COLLECTION_NAME,
                persist_directory=str(CHROMA_DIR)
            )
        else:
            # Subsequent batches - add to existing
            vector_store.add_documents(batch)
    
    logger.info(f"✅ Vector store built!")
    logger.info(f"📊 Location: {CHROMA_DIR}")
    logger.info(f"📊 Collection: {COLLECTION_NAME}")
    logger.info(f"📊 Total documents: {len(all_documents)}")
    
    # 5. Verification
    logger.info("\n" + "=" * 60)
    logger.info("🔍 Verifying Vector Store")
    logger.info("=" * 60)
    
    # Test retrieval 1: BTC technical analysis
    test_results_1 = vector_store.similarity_search(
        "BTC technical analysis price breakout",
        k=3,
        filter={"$and": [{"section": "BTC Analysis"}, {"analysis_type": "Technical Analysis"}]}
    )
    
    logger.info(f"\n✅ Test Query 1 (BTC Technical): {len(test_results_1)} results")
    if test_results_1:
        doc = test_results_1[0]
        logger.info(f"   - Date: {doc.metadata.get('date')}")
        logger.info(f"   - Type: {doc.metadata.get('analysis_type')}")
        logger.info(f"   - Preview: {doc.page_content[:100]}...")
    
    # Test retrieval 2: Capital flow
    test_results_2 = vector_store.similarity_search(
        "ETF capital flow analysis",
        k=2,
        filter={"$and": [{"section": "BTC Analysis"}, {"analysis_type": "Capital Flow"}]}
    )
    
    logger.info(f"\n✅ Test Query 2 (ETF Flow): {len(test_results_2)} results")
    if test_results_2:
        doc = test_results_2[0]
        logger.info(f"   - Date: {doc.metadata.get('date')}")
        logger.info(f"   - Preview: {doc.page_content[:100]}...")
    
    # Statistics
    logger.info("\n" + "=" * 60)
    logger.info("📈 Vector Store Statistics")
    logger.info("=" * 60)
    
    sections = {}
    analysis_types = {}
    
    for doc in all_documents:
        section = doc.metadata.get("section", "Unknown")
        analysis_type = doc.metadata.get("analysis_type", "Unknown")
        
        sections[section] = sections.get(section, 0) + 1
        analysis_types[analysis_type] = analysis_types.get(analysis_type, 0) + 1
    
    logger.info(f"\n📊 Section Distribution:")
    for section, count in sorted(sections.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"   - {section}: {count} documents")
    
    logger.info(f"\n📊 Analysis Type Distribution:")
    for analysis_type, count in sorted(analysis_types.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"   - {analysis_type}: {count} documents")
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 Vector store build complete! Ready to use RAG")
    logger.info("=" * 60)


if __name__ == "__main__":
    build_vector_store()
