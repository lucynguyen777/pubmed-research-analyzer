import pytest
import pandas as pd
from app.intelligence.topic_modeling import TopicModeler

@pytest.fixture
def mock_df():
    return pd.DataFrame({
        'pmid': ['111', '222', '333', '444', '555', '666'],
        'title': ['mRNA vaccine efficacy', 'COVID-19 transmission', 'Vaccine delivery mechanisms', 'Viral spread modeling', 'Lipid nanoparticle design', 'Epidemiology of coronavirus'],
        'abstract': ['Study on mRNA lipid nanoparticles', 'How virus spreads in populations', 'Lipid nanoparticles for delivery of mRNA', 'Modeling transmission dynamics', 'Engineering lipid nanoparticles', 'Global transmission statistics'],
    })

def test_topic_modeler_init():
    modeler = TopicModeler(n_topics=3)
    assert modeler.target_n_topics == 3
    assert not modeler.is_fitted

def test_topic_modeler_empty_df():
    modeler = TopicModeler()
    assert modeler.fit(pd.DataFrame()) == False
    assert not modeler.is_fitted

def test_topic_modeler_fit_and_extract(mock_df):
    modeler = TopicModeler(n_topics=2)
    success = modeler.fit(mock_df)
    
    assert success
    assert modeler.is_fitted
    assert modeler.n_topics_ == 2
    
    # Test word extraction
    words = modeler.get_topic_words(top_n=3)
    assert len(words) == 2
    assert len(words[0]) <= 3
    
    # Test document topics
    doc_topics = modeler.get_document_topics()
    assert not doc_topics.empty
    assert 'Topic_ID' in doc_topics.columns
    assert 'Topic_Confidence' in doc_topics.columns
    assert len(doc_topics) == len(mock_df)
    
    # Test distribution
    dist = modeler.get_topic_distribution()
    assert sum(dist.values()) == len(mock_df)
