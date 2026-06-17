"""
Topic Modeling Module.
Extracts latent research themes from document corpora using NMF.
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF

logger = logging.getLogger(__name__)

class TopicModeler:
    """Extracts topics from research articles using Non-negative Matrix Factorization."""

    def __init__(self, n_topics: int = 5):
        """
        Initialize the topic modeler.
        
        Args:
            n_topics: Number of distinct topics to discover.
        """
        self.target_n_topics = n_topics
        self.n_topics_ = n_topics
        self.is_fitted = False
        
        self.vectorizer = TfidfVectorizer(
            max_df=0.95, 
            min_df=2,
            stop_words='english',
            max_features=2000
        )
        self.model = None
        self.df: Optional[pd.DataFrame] = None
        
        # Output artifacts
        self.topic_assignments: List[int] = []
        self.topic_scores: np.ndarray = np.array([])
        self.feature_names: List[str] = []

    def fit(self, df: pd.DataFrame) -> bool:
        """
        Fit the NMF model to a dataframe of articles.
        
        Args:
            df: DataFrame with 'pmid', 'title', 'abstract'
            
        Returns:
            bool: Success status
        """
        if df is None or df.empty:
            logger.warning("Empty DataFrame provided to TopicModeler")
            return False
            
        # Dynamically adjust topics if we have very few papers
        self.n_topics_ = min(self.target_n_topics, max(2, len(df) // 3))
        if len(df) < 5:
            logger.warning(f"Very few documents ({len(df)}). Topic modeling might be unstable.")
            self.n_topics_ = max(1, len(df) // 2)

        self.df = df.copy()
        texts = []
        for _, row in self.df.iterrows():
            title = str(row.get('title', ''))
            abstract = str(row.get('abstract', ''))
            texts.append(f"{title}. {abstract}")

        try:
            # 1. TF-IDF Representation
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            self.feature_names = self.vectorizer.get_feature_names_out().tolist()

            # 2. NMF Factorization
            self.model = NMF(
                n_components=self.n_topics_, 
                random_state=42,
                init='nndsvda',
                max_iter=500
            )
            
            # W matrix: Document-Topic distribution
            self.topic_scores = self.model.fit_transform(tfidf_matrix)
            
            # Extract dominant topic per document
            if self.topic_scores.shape[1] > 0:
                self.topic_assignments = self.topic_scores.argmax(axis=1).tolist()
            else:
                self.topic_assignments = [0] * len(df)

            self.is_fitted = True
            logger.info(f"Successfully extracted {self.n_topics_} topics from {len(texts)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error during topic modeling: {e}")
            self.is_fitted = False
            return False

    def get_topic_words(self, top_n: int = 10) -> Dict[int, List[str]]:
        """
        Get the most representative words for each topic.
        
        Args:
            top_n: Number of keywords per topic
            
        Returns:
            Dict mapping topic index to list of keywords
        """
        if not self.is_fitted or self.model is None:
            return {}
            
        topics = {}
        # H matrix: Topic-Term distribution
        for topic_idx, topic_weights in enumerate(self.model.components_):
            top_word_indices = topic_weights.argsort()[:-top_n - 1:-1]
            topics[topic_idx] = [self.feature_names[i] for i in top_word_indices]
            
        return topics

    def get_document_topics(self) -> pd.DataFrame:
        """
        Return the original dataframe augmented with topic assignments.
        """
        if not self.is_fitted or self.df is None:
            return pd.DataFrame()
            
        result = self.df.copy()
        result['Topic_ID'] = self.topic_assignments
        
        # Calculate confidence score (weight of the dominant topic)
        confidence = self.topic_scores.max(axis=1)
        result['Topic_Confidence'] = confidence
        
        return result

    def get_topic_distribution(self) -> Dict[int, int]:
        """
        Get the count of documents per topic.
        """
        if not self.is_fitted:
            return {}
            
        counts = pd.Series(self.topic_assignments).value_counts()
        return {int(k): int(v) for k, v in counts.items()}
