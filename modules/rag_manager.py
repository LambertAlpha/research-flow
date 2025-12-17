#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG Manager Module
Manages retrieval of historical report analysis patterns for style learning
"""

import os
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class RAGManager:
    """RAG Knowledge Base Manager"""

    def __init__(
        self,
        chroma_dir: str = "./chroma_db",
        collection_name: str = "crypto_weekly_reports",
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize RAG Manager

        Args:
            chroma_dir: ChromaDB persistence directory
            collection_name: Collection name
            embedding_model: OpenAI Embedding model
        """
        self.chroma_dir = chroma_dir
        self.collection_name = collection_name

        # Initialize Embedding (use EMBEDDING env var if available)
        embedding_api_key = os.getenv("EMBEDDING") or os.getenv("EMBEDDINGS") or os.getenv("OPENAI_API_KEY")
        self.embeddings = OpenAIEmbeddings(model=embedding_model, openai_api_key=embedding_api_key)

        # Load VectorStore
        self.vector_store = self._init_vector_store()

        logger.info(f"✅ RAG Manager initialized, Collection: {collection_name}")

    def _init_vector_store(self) -> Chroma:
        """Initialize vector database"""
        if os.path.exists(self.chroma_dir):
            # Load existing vector store
            logger.info(f"Loading existing vector store: {self.chroma_dir}")
            return Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.chroma_dir
            )
        else:
            # Vector store doesn't exist
            logger.warning(f"Vector store not found: {self.chroma_dir}")
            logger.warning("Please run scripts/build_vector_store.py first")
            raise FileNotFoundError(f"Vector store not found: {self.chroma_dir}")

    def retrieve_context(
        self,
        prompt_type: str,
        current_data: Dict,
        time_decay_days: int = 90
    ) -> Dict[str, str]:
        """
        Retrieve relevant historical report segments for style learning

        Args:
            prompt_type: Content type ("btc_analysis", "macro_analysis", etc.)
            current_data: Current data (used to build Query)
            time_decay_days: Time decay half-life

        Returns:
            {
                "style_guide": "Combined reference content (for Prompt)",
                "reasoning_examples": "Reasoning logic examples (for meta-cognition)"
            }
        """
        # Step 1: Build multiple retrieval queries
        queries = self._build_queries(prompt_type, current_data)

        # Step 2: Execute retrieval
        all_results = []
        for query_config in queries:
            try:
                results = self.vector_store.similarity_search(
                    query=query_config["query"],
                    k=query_config["k"],
                    filter=query_config.get("filter", {})
                )
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Retrieval query failed: {query_config['query']}, Error: {e}")
                continue

        # Step 3: Time decay reranking
        ranked_results = self._apply_time_decay(all_results, time_decay_days)

        # Step 4: Assemble context
        context = self._assemble_context(ranked_results, prompt_type)

        logger.info(f"✅ [RAG] Retrieved {len(ranked_results)} reference segments for {prompt_type}")
        return context

    def _build_queries(self, prompt_type: str, current_data: Dict) -> List[Dict]:
        """Build retrieval queries (Multi-Query strategy)"""

        if prompt_type == "btc_analysis":
            # Get current data features
            current_price = current_data.get("current_price", 0)
            ma7 = current_data.get("ma7", 0)
            trend = "rising" if current_price > ma7 else "falling"

            return [
                # Query 1: Technical analysis (retrieve similar trends)
                {
                    "query": f"BTC {trend} technical analysis key support resistance levels",
                    "filter": {
                        "$and": [
                            {"section": "BTC Analysis"},
                            {"analysis_type": "Technical Analysis"},
                            {"granularity": "fine"}
                        ]
                    },
                    "k": 2  # Only 2 typical cases
                },

                # Query 2: Capital flow (retrieve funding logic)
                {
                    "query": "BTC ETF capital flow relationship with price trends",
                    "filter": {
                        "$and": [
                            {"section": "BTC Analysis"},
                            {"analysis_type": "Capital Flow"},
                            {"granularity": "fine"}
                        ]
                    },
                    "k": 2
                },

                # Query 3: Derivatives (retrieve market sentiment indicators)
                {
                    "query": "BTC futures options data reflecting market sentiment",
                    "filter": {
                        "$and": [
                            {"section": "BTC Analysis"},
                            {"analysis_type": "Derivatives"},
                            {"granularity": "fine"}
                        ]
                    },
                    "k": 1
                },

                # Query 4: Complete context (coarse-grained)
                {
                    "query": "BTC complete weekly report analysis framework",
                    "filter": {
                        "$and": [
                            {"section": "BTC Analysis"},
                            {"granularity": "coarse"}
                        ]
                    },
                    "k": 1
                }
            ]

        elif prompt_type == "macro_analysis":
            return [
                {
                    "query": "USD index Treasury yields impact on crypto markets",
                    "filter": {"$and": [{"section": "Macro"}, {"analysis_type": "Macro Environment"}]},
                    "k": 2
                },
                {
                    "query": "Nvidia crypto-related stocks BTC correlation analysis",
                    "filter": {"$and": [{"section": "Macro"}, {"analysis_type": "Related Assets"}]},
                    "k": 2
                }
            ]

        # Default: generic query
        return [{
            "query": f"{prompt_type} market analysis",
            "filter": {},
            "k": 3
        }]

    def _apply_time_decay(self, results: List[Document], decay_days: int) -> List[Document]:
        """
        Apply time decay to retrieval results, prioritize recent reports

        Args:
            results: Retrieval results
            decay_days: Half-life (weight drops to 50% after this many days)
        """
        now = datetime.now()

        for doc in results:
            try:
                doc_date = datetime.strptime(doc.metadata["date"], "%Y-%m-%d")
                days_ago = (now - doc_date).days

                # Exponential decay: score_new = score_original * exp(-days_ago / decay_days)
                time_weight = 2 ** (-days_ago / decay_days)

                # Note: similarity_search doesn't return scores by default
                # If needed, use similarity_search_with_score
                doc.metadata["time_weight"] = time_weight

            except Exception as e:
                logger.warning(f"Time decay calculation failed: {e}")
                doc.metadata["time_weight"] = 1.0

        # Sort by time weight (prioritize recent)
        results.sort(key=lambda x: x.metadata.get("time_weight", 0), reverse=True)
        return results

    def _assemble_context(self, results: List[Document], prompt_type: str) -> Dict[str, str]:
        """
        Assemble context into Prompt-usable format

        Core logic: Two-Step RAG
        """
        if not results:
            return {
                "style_guide": "",
                "reasoning_examples": ""
            }

        # Group by analysis_type
        grouped = {}
        for doc in results:
            analysis_type = doc.metadata.get("analysis_type", "Other")
            if analysis_type not in grouped:
                grouped[analysis_type] = []
            grouped[analysis_type].append(doc.page_content)

        # Assemble reasoning_examples (for meta-cognition)
        reasoning_examples = []
        for analysis_type, texts in grouped.items():
            reasoning_examples.append(f"## {analysis_type} Dimension Reasoning Example:")
            reasoning_examples.append(texts[0])  # Only take most relevant 1

        # Assemble style_guide (complete reference)
        style_guide = "\n\n---\n\n".join([
            f"[Reference Segment {i+1}] ({doc.metadata.get('analysis_type', '')} - {doc.metadata.get('date', '')})\n{doc.page_content}"
            for i, doc in enumerate(results[:5])  # Max 5 segments
        ])

        return {
            "style_guide": style_guide,
            "reasoning_examples": "\n\n".join(reasoning_examples)
        }

    def get_stats(self) -> Dict:
        """Get vector store statistics"""
        try:
            collection = self.vector_store._collection
            count = collection.count()

            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
                "chroma_dir": self.chroma_dir
            }
        except Exception as e:
            logger.warning(f"Failed to get stats: {e}")
            return {
                "total_chunks": 0,
                "collection_name": self.collection_name,
                "chroma_dir": self.chroma_dir
            }
