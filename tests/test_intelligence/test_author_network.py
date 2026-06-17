import pytest
import pandas as pd
import networkx as nx
from app.intelligence.author_network import AuthorNetworkBuilder, AuthorAnalyzer

@pytest.fixture
def mock_author_df():
    return pd.DataFrame({
        'authors': [
            ['Alice', 'Bob', 'Charlie'],
            ['Alice', 'David'],
            ['Bob', 'Charlie', 'Eve'],
            ['Eve', 'Frank'],
            ['David', 'Frank', 'Grace'],
            ['Alice', 'Grace']
        ]
    })

def test_author_network_builder(mock_author_df):
    builder = AuthorNetworkBuilder()
    graph = builder.build_network(mock_author_df)
    
    assert graph.number_of_nodes() == 7  # Alice, Bob, Charlie, David, Eve, Frank, Grace
    assert graph.number_of_edges() > 0
    assert graph['Alice']['Bob']['weight'] == 1
    assert graph['Alice']['Grace']['weight'] == 1
    assert graph['David']['Frank']['weight'] == 1

def test_author_analyzer_top_authors(mock_author_df):
    builder = AuthorNetworkBuilder()
    graph = builder.build_network(mock_author_df)
    analyzer = AuthorAnalyzer(graph)
    
    top_authors = analyzer.get_top_authors(metric="degree", top_n=3)
    assert len(top_authors) == 3
    assert top_authors[0][0] == 'Alice'  # Alice has the highest degree centrality

def test_author_analyzer_communities(mock_author_df):
    builder = AuthorNetworkBuilder()
    graph = builder.build_network(mock_author_df)
    analyzer = AuthorAnalyzer(graph)
    
    communities = analyzer.detect_research_groups()
    assert len(communities) > 0
    assert any('Alice' in community for community in communities)

def test_author_analyzer_author_stats(mock_author_df):
    builder = AuthorNetworkBuilder()
    graph = builder.build_network(mock_author_df)
    analyzer = AuthorAnalyzer(graph)
    
    stats = analyzer.get_author_stats('Alice')
    assert stats['Publication Count'] > 0
    assert stats['Collaboration Count'] > 0
    assert stats['H-Index Approximation'] > 0

def test_author_analyzer_collaboration_path(mock_author_df):
    builder = AuthorNetworkBuilder()
    graph = builder.build_network(mock_author_df)
    analyzer = AuthorAnalyzer(graph)
    
    path = analyzer.find_collaboration_path('Alice', 'Frank')
    assert path == ['Alice', 'Grace', 'Frank'] or path == ['Alice', 'David', 'Frank']
