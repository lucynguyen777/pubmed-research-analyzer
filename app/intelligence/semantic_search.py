"""
Semantic Search Intelligence Module.
Replaces keyword-matching with semantic similarity search.
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer  # pyright: ignore[reportMissingImports]
    import faiss  # pyright: ignore[reportMissingImports]
    from sklearn.feature_extraction.text import TfidfVectorizer  # pyright: ignore[reportMissingImports]
    from sklearn.metrics.pairwise import cosine_similarity  # pyright: ignore[reportMissingImports]

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer  # pyright: ignore[reportMissingImports]
    import faiss  # pyright: ignore[reportMissingImports]
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    logger.warning("sentence-transformers or faiss not installed. Falling back to TF-IDF.")
    HAS_SENTENCE_TRANSFORMERS = False
    from sklearn.feature_extraction.text import TfidfVectorizer  # pyright: ignore[reportMissingImports]
    from sklearn.metrics.pairwise import cosine_similarity  # pyright: ignore[reportMissingImports]


class SemanticSearchEngine:
    """Engine for semantic similarity search of research papers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize semantic search engine.
        
        Args:
            model_name: HuggingFace sentence-transformers model name
        """
        self.is_ready = False
        self.df: Optional[pd.DataFrame] = None
        self.pmids: List[str] = []
        self.model: Any = None
        self.index: Any = None
        self.dimension: int = 0
        self._mode: str = "tfidf"
        self.vectorizer: Any = None
        self.tfidf_matrix: Any = None
        
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self.model = SentenceTransformer(model_name)
                self.index = None
                self.dimension = self.model.get_sentence_embedding_dimension()
                self._mode = "transformer"
            except Exception as e:
                logger.error(f"Failed to load sentence transformer: {e}. Falling back to TF-IDF.")
                self._init_tfidf()
        else:
            self._init_tfidf()

    def _init_tfidf(self):
        """Initialize TF-IDF fallback."""
        self._mode = "tfidf"
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        self.tfidf_matrix = None

    def _prepare_texts(self, df: pd.DataFrame) -> List[str]:
        """Combine title and abstract for embedding."""
        texts = []
        for _, row in df.iterrows():
            title = str(row.get('title', ''))
            abstract = str(row.get('abstract', ''))
            texts.append(f"{title}. {abstract}")
        return texts

    def build_index(self, df: pd.DataFrame) -> bool:
        """
        Build the search index from a DataFrame of articles.
        
        Args:
            df: DataFrame containing at least 'pmid', 'title', and 'abstract'
            
        Returns:
            bool: Success status
        """
        if df is None or df.empty:
            logger.warning("Empty DataFrame provided to build_index")
            return False
            
        self.df = df.copy()
        self.pmids = df['pmid'].tolist()
        texts = self._prepare_texts(df)
        
        try:
            if self._mode == "transformer":
                assert self.model is not None
                # Generate embeddings
                embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                faiss.normalize_L2(embeddings)
                
                # Build FAISS index
                self.index = faiss.IndexFlatIP(self.dimension)
                self.index.add(embeddings)
            else:
                # TF-IDF fallback
                self.tfidf_matrix = self.vectorizer.fit_transform(texts)
                
            self.is_ready = True
            logger.info(f"Successfully built {self._mode} index for {len(texts)} articles")
            return True
            
        except Exception as e:
            logger.error(f"Error building search index: {e}")
            self.is_ready = False
            return False

    def search(self, query: str, top_k: int = 10) -> pd.DataFrame:
        """
        Perform semantic search for a query.
        
        Args:
            query: Search string
            top_k: Number of results to return
            
        Returns:
            DataFrame of top results with similarity scores
        """
        if not self.is_ready or self.df is None or self.df.empty:
            logger.warning("Search engine not ready. Call build_index first.")
            return pd.DataFrame()
            
        if not query.strip():
            return pd.DataFrame()
            
        k = min(top_k, len(self.df))
        
        try:
            if self._mode == "transformer":
                assert self.model is not None
                assert self.index is not None
                query_vector = self.model.encode([query], convert_to_numpy=True)
                faiss.normalize_L2(query_vector)
                
                scores, indices = self.index.search(query_vector, k)
                
                results_idx = indices[0]
                similarity_scores = scores[0]
            else:
                assert self.vectorizer is not None
                assert self.tfidf_matrix is not None
                query_vec = self.vectorizer.transform([query])
                cosine_sim = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
                
                results_idx = cosine_sim.argsort()[-k:][::-1]
                similarity_scores = cosine_sim[results_idx]
                
            # Filter out zero similarity (for TF-IDF mostly)
            valid_mask = similarity_scores > 0
            if not valid_mask.any():
                return pd.DataFrame()
                
            results_idx = results_idx[valid_mask]
            similarity_scores = similarity_scores[valid_mask]
            
            # Construct results DataFrame
            results_df = self.df.iloc[results_idx].copy()
            results_df['similarity_score'] = similarity_scores
            
            return results_df
            
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            return pd.DataFrame()

    def find_similar_papers(self, pmid: str, top_k: int = 5) -> pd.DataFrame:
        """
        Find papers similar to a given article.
        
        Args:
            pmid: Target article PMID
            top_k: Number of similar papers to return
            
        Returns:
            DataFrame of similar papers with similarity scores
        """
        if not self.is_ready or self.df is None:
            return pd.DataFrame()
            
        if pmid not in self.pmids:
            logger.warning(f"PMID {pmid} not found in index")
            return pd.DataFrame()
            
        idx = self.pmids.index(pmid)
        # We search for top_k + 1 to account for the paper itself
        k = min(top_k + 1, len(self.df))
        
        try:
            if self._mode == "transformer":
                assert self.model is not None
                assert self.index is not None
                # Get the embedding for the target paper
                # For simplicity, we re-embed its text (or we could extract from FAISS if using IndexIVF, but FlatIP doesn't store easily)
                row = self.df.iloc[idx]
                text = f"{row.get('title', '')}. {row.get('abstract', '')}"
                
                query_vector = self.model.encode([text], convert_to_numpy=True)
                faiss.normalize_L2(query_vector)
                
                scores, indices = self.index.search(query_vector, k)
                results_idx = indices[0]
                similarity_scores = scores[0]
            else:
                assert self.tfidf_matrix is not None
                target_vec = self.tfidf_matrix[idx]
                cosine_sim = cosine_similarity(target_vec, self.tfidf_matrix).flatten()
                
                results_idx = cosine_sim.argsort()[-k:][::-1]
                similarity_scores = cosine_sim[results_idx]
                
            # Filter out the target paper itself and zero similarity
            mask = (results_idx != idx) & (similarity_scores > 0)
            results_idx = results_idx[mask][:top_k]
            similarity_scores = similarity_scores[mask][:top_k]
            
            if len(results_idx) == 0:
                return pd.DataFrame()
                
            # Construct results DataFrame
            results_df = self.df.iloc[results_idx].copy()
            results_df['similarity_score'] = similarity_scores
            
            return results_df
            
        except Exception as e:
            logger.error(f"Error finding similar papers: {e}")
            return pd.DataFrame()