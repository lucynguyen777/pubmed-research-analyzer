import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from app.intelligence.semantic_search import SemanticSearchEngine, HAS_SENTENCE_TRANSFORMERS

@pytest.fixture
def mock_df():
    return pd.DataFrame({
        'pmid': ['111', '222', '333'],
        'title': ['mRNA vaccine efficacy', 'COVID-19 transmission', 'Vaccine delivery mechanisms'],
        'abstract': ['Study on mRNA', 'How virus spreads', 'Lipid nanoparticles for delivery'],
        'journal': ['Nature', 'Science', 'Cell'],
        'pub_date': ['2021', '2020', '2022']
    })

def test_engine_init_tfidf():
    """Test TF-IDF fallback initialization."""
    with patch('app.intelligence.semantic_search.HAS_SENTENCE_TRANSFORMERS', False):
        engine = SemanticSearchEngine()
        assert engine._mode == "tfidf"
        assert engine.vectorizer is not None
        assert not engine.is_ready

def test_engine_build_index_empty():
    engine = SemanticSearchEngine()
    assert engine.build_index(pd.DataFrame()) == False
    assert not engine.is_ready

def test_engine_build_and_search_tfidf(mock_df):
    """Test full pipeline using TF-IDF mode."""
    engine = SemanticSearchEngine()
    engine._mode = "tfidf"
    engine._init_tfidf()
    
    success = engine.build_index(mock_df)
    assert success
    assert engine.is_ready
    assert engine.tfidf_matrix is not None
    
    # Test search
    results = engine.search("mRNA vaccine", top_k=2)
    assert not results.empty
    assert len(results) <= 2
    assert 'similarity_score' in results.columns
    
    # Test find similar
    similar = engine.find_similar_papers('111', top_k=1)
    assert not similar.empty
    # The most similar to 'mRNA vaccine efficacy' should be 'Vaccine delivery mechanisms' due to 'vaccine' match
    assert similar.iloc[0]['pmid'] == '333'

def test_search_not_ready():
    engine = SemanticSearchEngine()
    results = engine.search("query")
    assert results.empty
