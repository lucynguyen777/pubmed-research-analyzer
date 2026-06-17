"""
Author Collaboration Network Module.
Builds and analyzes networks of co-authors to identify influential researchers and research groups.
"""

import networkx as nx
import pandas as pd
from typing import List, Dict, Set, Tuple
from networkx.algorithms.community import greedy_modularity_communities

class AuthorNetworkBuilder:
    """Builds a co-authorship network from publication data."""

    def __init__(self):
        """Initialize the network builder."""
        self.graph = nx.Graph()

    def build_network(self, df: pd.DataFrame) -> nx.Graph:
        """
        Build a co-authorship network from a DataFrame.
        
        Args:
            df: DataFrame with 'authors' column (list of authors per paper).
        
        Returns:
            nx.Graph: Co-authorship network.
        """
        if 'authors' not in df.columns:
            raise ValueError("DataFrame must contain an 'authors' column.")
        
        for _, row in df.iterrows():
            authors = row['authors']
            if isinstance(authors, list) and len(authors) > 1:
                for i, author1 in enumerate(authors):
                    for author2 in authors[i + 1:]:
                        if self.graph.has_edge(author1, author2):
                            self.graph[author1][author2]['weight'] += 1
                        else:
                            self.graph.add_edge(author1, author2, weight=1)
        
        return self.graph


class AuthorAnalyzer:
    """Analyzes the co-authorship network."""

    def __init__(self, graph: nx.Graph):
        """
        Initialize the analyzer with a co-authorship graph.
        
        Args:
            graph: Co-authorship network.
        """
        self.graph = graph

    def get_top_authors(self, metric: str = "degree", top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Get top authors based on a centrality metric.
        
        Args:
            metric: Centrality metric ('degree', 'betweenness', 'closeness').
            top_n: Number of top authors to return.
        
        Returns:
            List of tuples (author, score).
        """
        if metric == "degree":
            centrality = nx.degree_centrality(self.graph)
        elif metric == "betweenness":
            centrality = nx.betweenness_centrality(self.graph)
        elif metric == "closeness":
            centrality = nx.closeness_centrality(self.graph)
        else:
            raise ValueError("Invalid metric. Choose from 'degree', 'betweenness', 'closeness'.")
        
        return sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def detect_research_groups(self) -> List[Set[str]]:
        """
        Detect research groups using community detection.
        
        Returns:
            List of sets, where each set contains authors in a community.
        """
        return list(greedy_modularity_communities(self.graph))

    def get_author_stats(self, author_name: str) -> Dict:
        """
        Get statistics for a specific author.
        
        Args:
            author_name: Name of the author.
        
        Returns:
            Dictionary with publication count, collaboration count, and h-index approximation.
        """
        if author_name not in self.graph:
            return {}
        
        neighbors = list(self.graph.neighbors(author_name))
        collaboration_count = len(neighbors)
        publication_count = sum(self.graph[author_name][neighbor]['weight'] for neighbor in neighbors)
        
        # Approximate h-index: count of neighbors with weight >= k
        weights = sorted([self.graph[author_name][neighbor]['weight'] for neighbor in neighbors], reverse=True)
        h_index = sum(1 for i, w in enumerate(weights, 1) if w >= i)
        
        return {
            "Publication Count": publication_count,
            "Collaboration Count": collaboration_count,
            "H-Index Approximation": h_index
        }

    def find_collaboration_path(self, author1: str, author2: str) -> List[str]:
        """
        Find the shortest collaboration path between two authors.
        
        Args:
            author1: Name of the first author.
            author2: Name of the second author.
        
        Returns:
            List of authors in the path, or an empty list if no path exists.
        """
        try:
            return nx.shortest_path(self.graph, source=author1, target=author2)
        except nx.NetworkXNoPath:
            return []