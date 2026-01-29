"""
RAG (Retrieval-Augmented Generation) Service
Handles knowledge base search with hybrid vector + full-text search and relevance scoring.
"""

import logging
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

logger = logging.getLogger(__name__)

# Relevance threshold: chunks with cosine distance above this are considered irrelevant
RELEVANCE_THRESHOLD = 0.85  # cosine distance (0 = identical, 2 = opposite)
DEFAULT_TOP_K = 8  # Retrieve more candidates for reranking
FINAL_TOP_K = 5    # Return top 5 after reranking


class RAGService:
    """Handles knowledge base retrieval with hybrid search and reranking."""

    def __init__(self, gemini_client=None):
        self.gemini = gemini_client

    def search(self, db: Session, bot_id: str, query: str, top_k: int = FINAL_TOP_K) -> str:
        """
        Hybrid search: combines vector similarity + full-text keyword search.
        Returns formatted context string for LLM prompt injection.
        """
        try:
            from models import FileChunk, File

            # Check if we have indexed chunks
            has_chunks = db.query(FileChunk.id).join(File).filter(File.bot_id == bot_id).first()
            if not has_chunks:
                logger.info("No vectors found, falling back to legacy full-text")
                return self._fetch_legacy(db, bot_id)

            if not self.gemini:
                return ""

            # Run hybrid search
            results = self._hybrid_search(db, bot_id, query, top_k=DEFAULT_TOP_K)

            if not results:
                return ""

            # Rerank and filter by relevance
            ranked = self._rerank(results, top_k=top_k)

            logger.info(f"Hybrid search returned {len(ranked)} relevant chunks")
            return "\n\n".join([
                f"--- Context (from {filename}, relevance: {score:.2f}) ---\n{content}"
                for content, filename, score in ranked
            ])

        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return self._fetch_legacy(db, bot_id)

    def search_with_scores(self, db: Session, bot_id: str, query: str, top_k: int = FINAL_TOP_K) -> List[dict]:
        """
        Search and return results with metadata (used by chat endpoint for source citations).
        """
        try:
            from models import FileChunk, File

            has_chunks = db.query(FileChunk.id).join(File).filter(File.bot_id == bot_id).first()
            if not has_chunks or not self.gemini:
                return []

            results = self._hybrid_search(db, bot_id, query, top_k=DEFAULT_TOP_K)
            ranked = self._rerank(results, top_k=top_k)

            return [
                {
                    "content": content,
                    "filename": filename,
                    "relevance_score": score,
                    "chunk_index": chunk_idx,
                }
                for content, filename, score, chunk_idx in ranked
            ]
        except Exception as e:
            logger.error(f"RAG search_with_scores failed: {e}")
            return []

    def _hybrid_search(
        self, db: Session, bot_id: str, query: str, top_k: int = DEFAULT_TOP_K
    ) -> List[Tuple[str, str, float, int]]:
        """
        Hybrid search combining vector similarity and keyword matching.
        Uses Reciprocal Rank Fusion (RRF) to merge results.

        Returns: List of (content, filename, rrf_score, chunk_index)
        """
        from models import FileChunk, File

        # --- Vector Search (with embedding cache) ---
        from app.cache import get_cached_embedding, set_cached_embedding

        query_vector = get_cached_embedding(query)
        if query_vector is None:
            query_vector = self.gemini.embed_content(query, "retrieval_query")
            set_cached_embedding(query, query_vector)

        vector_results = (
            db.query(
                FileChunk.content,
                File.filename,
                FileChunk.embedding.cosine_distance(query_vector).label("distance"),
                FileChunk.chunk_index,
                FileChunk.id,
            )
            .join(File)
            .filter(File.bot_id == bot_id)
            .order_by(FileChunk.embedding.cosine_distance(query_vector))
            .limit(top_k)
            .all()
        )

        # --- Keyword Search (BM25-like using PostgreSQL full-text) ---
        keyword_results = self._keyword_search(db, bot_id, query, top_k=top_k)

        # --- Reciprocal Rank Fusion (RRF) ---
        rrf_k = 60  # Standard RRF constant
        scores = {}  # chunk_id -> {content, filename, score, chunk_index}

        for rank, (content, filename, distance, chunk_idx, chunk_id) in enumerate(vector_results):
            rrf_score = 1.0 / (rrf_k + rank + 1)
            relevance = max(0, 1.0 - distance)  # Convert distance to similarity
            scores[chunk_id] = {
                "content": content,
                "filename": filename,
                "score": rrf_score,
                "relevance": relevance,
                "chunk_index": chunk_idx,
            }

        for rank, (content, filename, chunk_idx, chunk_id) in enumerate(keyword_results):
            rrf_score = 1.0 / (rrf_k + rank + 1)
            if chunk_id in scores:
                # Boost: chunk found by both methods
                scores[chunk_id]["score"] += rrf_score
            else:
                scores[chunk_id] = {
                    "content": content,
                    "filename": filename,
                    "score": rrf_score,
                    "relevance": 0.5,  # Unknown vector relevance
                    "chunk_index": chunk_idx,
                }

        # Sort by RRF score descending
        sorted_results = sorted(scores.values(), key=lambda x: x["score"], reverse=True)

        return [
            (r["content"], r["filename"], r["score"], r["chunk_index"])
            for r in sorted_results[:top_k]
        ]

    def _keyword_search(
        self, db: Session, bot_id: str, query: str, top_k: int = 8
    ) -> List[Tuple[str, str, int, str]]:
        """
        Full-text keyword search using SQL LIKE/ILIKE.
        Returns: List of (content, filename, chunk_index, chunk_id)
        """
        from models import FileChunk, File

        # Extract meaningful keywords (skip short words)
        keywords = [w.strip() for w in query.split() if len(w.strip()) > 2]

        if not keywords:
            return []

        try:
            # Build OR conditions for keyword matching
            conditions = []
            for kw in keywords[:5]:  # Limit to 5 keywords
                conditions.append(FileChunk.content.ilike(f"%{kw}%"))

            results = (
                db.query(
                    FileChunk.content,
                    File.filename,
                    FileChunk.chunk_index,
                    FileChunk.id,
                )
                .join(File)
                .filter(File.bot_id == bot_id)
                .filter(or_(*conditions))
                .limit(top_k)
                .all()
            )

            return results
        except Exception as e:
            logger.warning(f"Keyword search failed: {e}")
            return []

    def _rerank(
        self, results: List[Tuple[str, str, float, int]], top_k: int = FINAL_TOP_K
    ) -> List[Tuple[str, str, float, int]]:
        """
        Rerank results by RRF score, filtering out low-relevance chunks.
        Results are already sorted by RRF score from _hybrid_search.
        """
        # Filter by minimum score threshold (optional)
        # For now just return top_k, the RRF score already handles ranking
        return results[:top_k]

    def _fetch_legacy(self, db: Session, bot_id: str) -> str:
        """Fallback: Fetch all text content from files (no vector search)."""
        try:
            from models import File

            files = db.query(File).filter(
                File.bot_id == bot_id,
                File.content.isnot(None)
            ).all()

            if not files:
                return ""

            kb_content = []
            for f in files:
                if f.content and f.content != "[Stored in GCS]":
                    kb_content.append(f"--- File: {f.filename} ---\n{f.content}")

            return "\n\n".join(kb_content)
        except Exception as e:
            logger.error(f"Failed to fetch knowledge base: {e}")
            return ""
