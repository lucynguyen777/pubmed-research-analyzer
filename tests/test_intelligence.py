"""
Unit tests for the intelligence module (citation network analysis).
"""

import pytest
import networkx as nx
import pandas as pd
from unittest.mock import patch, MagicMock

from app.intelligence.citation_network import (
    CitationNetworkBuilder,
    NetworkAnalyzer,
    NetworkVisualizer,
)


class TestCitationNetworkBuilder:
    """Tests for CitationNetworkBuilder."""

    def setup_method(self):
        self.builder = CitationNetworkBuilder()

    def test_initial_state(self):
        """Builder initializes with empty graph."""
        assert self.builder.graph.number_of_nodes() == 0
        assert self.builder.graph.number_of_edges() == 0
        assert self.builder.metadata == {}

    def test_build_empty_list(self):
        """Building with empty PMID list produces empty graph."""
        graph = self.builder.build_network([])
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0

    def test_build_single_paper_no_citations(self):
        """Single paper without citations creates single-node graph."""
        pmids = ["12345"]
        with patch.object(self.builder, "_extract_citations_for_paper") as mock:
            mock.return_value = {"references": [], "cited_by": []}
            graph = self.builder.build_network(pmids)

        assert graph.number_of_nodes() == 1
        assert "12345" in graph.nodes()
        assert graph.nodes["12345"].get("seed") is True

    def test_build_with_references(self):
        """References create edges from seed paper to referenced papers."""
        pmids = ["12345"]
        with patch.object(self.builder, "_extract_citations_for_paper") as mock:
            mock.return_value = {"references": ["67890", "11111"], "cited_by": []}
            graph = self.builder.build_network(pmids)

        assert graph.number_of_nodes() == 3
        assert graph.has_edge("12345", "67890")
        assert graph.has_edge("12345", "11111")

    def test_build_with_cited_by(self):
        """Cited-by papers create edges to seed paper."""
        pmids = ["12345"]
        with patch.object(self.builder, "_extract_citations_for_paper") as mock:
            mock.return_value = {"references": [], "cited_by": ["99999"]}
            graph = self.builder.build_network(pmids)

        assert graph.number_of_nodes() == 2
        assert graph.has_edge("99999", "12345")

    def test_build_network_stats(self):
        """Network stats are computed after build."""
        pmids = ["12345"]
        with patch.object(self.builder, "_extract_citations_for_paper") as mock:
            mock.return_value = {"references": ["67890"], "cited_by": ["99999"]}
            self.builder.build_network(pmids)

        stats = self.builder.get_network_stats()
        assert stats["Papers in network"] == 3
        assert stats["Citation links"] == 2

    def test_duplicate_pmids(self):
        """Duplicate PMIDs are deduplicated."""
        with patch.object(self.builder, "_extract_citations_for_paper") as mock:
            mock.return_value = {"references": [], "cited_by": []}
            graph = self.builder.build_network(["12345", "12345", "12345"])
        assert graph.number_of_nodes() == 1

    def test_add_papers_incremental(self):
        """Adding papers after initial build extends the graph."""
        with patch.object(self.builder, "_extract_citations_for_paper") as mock:
            mock.return_value = {"references": [], "cited_by": []}
            self.builder.build_network(["12345"])

        assert self.builder.graph.number_of_nodes() == 1

        with patch.object(self.builder, "_extract_citations_for_paper") as mock:
            mock.return_value = {"references": ["67890"], "cited_by": []}
            self.builder.add_papers(["99999"])

        assert self.builder.graph.number_of_nodes() >= 2

    def test_extract_citations_api_failure(self):
        """API failure returns empty citations gracefully."""
        result = self.builder._extract_citations_for_paper("invalid")
        assert result == {"references": [], "cited_by": []}


class TestNetworkAnalyzer:
    """Tests for NetworkAnalyzer."""

    def setup_method(self):
        self.graph = nx.DiGraph()
        # Simple chain: A -> B -> C
        self.graph.add_edge("A", "B")
        self.graph.add_edge("B", "C")
        self.analyzer = NetworkAnalyzer(self.graph)

    def test_calculate_all_metrics(self):
        """All metrics are computed for every node."""
        metrics = self.analyzer.calculate_all_metrics()
        assert len(metrics) == 3
        for node in ["A", "B", "C"]:
            assert node in metrics
            assert "pagerank" in metrics[node]
            assert "degree_centrality" in metrics[node]
            assert "betweenness" in metrics[node]
            assert "closeness" in metrics[node]
            assert "in_degree" in metrics[node]
            assert "out_degree" in metrics[node]

    def test_empty_graph_metrics(self):
        """Empty graph returns empty metrics."""
        empty_analyzer = NetworkAnalyzer(nx.DiGraph())
        metrics = empty_analyzer.calculate_all_metrics()
        assert metrics == {}

    def test_pagerank_values(self):
        """PageRank sums to ~1.0 (within tolerance)."""
        self.analyzer.calculate_all_metrics()
        pagerank_sum = sum(
            m["pagerank"] for m in self.analyzer.metrics.values()
        )
        assert abs(pagerank_sum - 1.0) < 0.01

    def test_degree_centrality(self):
        """Node A in chain A->B->C has out-degree, C has in-degree."""
        self.analyzer.calculate_all_metrics()
        assert self.analyzer.metrics["A"]["out_degree"] == 1
        assert self.analyzer.metrics["A"]["in_degree"] == 0
        assert self.analyzer.metrics["C"]["in_degree"] == 1
        assert self.analyzer.metrics["C"]["out_degree"] == 0

    def test_identify_influential_papers(self):
        """Returns top-N papers by each metric."""
        self.analyzer.calculate_all_metrics()
        influential = self.analyzer.identify_influential_papers(top_n=2)
        assert "pagerank" in influential
        assert "most_cited" in influential
        assert "bridges" in influential
        assert "central" in influential
        assert len(influential["pagerank"]) <= 2

    def test_summary_dataframe(self):
        """Summary returns DataFrame with correct columns."""
        self.analyzer.calculate_all_metrics()
        df = self.analyzer.summarize()
        assert isinstance(df, pd.DataFrame)
        expected_cols = [
            "pmid", "pagerank", "degree_centrality",
            "betweenness", "closeness", "in_degree",
            "out_degree", "total_degree"
        ]
        for col in expected_cols:
            assert col in df.columns

    def test_community_detection_import_error(self):
        """Community detection handles missing python-louvain gracefully."""
        communities = self.analyzer.detect_communities()
        # Should return empty dict if louvain not installed or no graph
        assert isinstance(communities, dict)


class TestNetworkVisualizer:
    """Tests for NetworkVisualizer."""

    def setup_method(self):
        self.graph = nx.DiGraph()
        self.graph.add_edge("A", "B")
        self.graph.add_edge("B", "C")
        self.metrics = {
            "A": {
                "pagerank": 0.4, "degree_centrality": 0.5,
                "betweenness": 0.0, "closeness": 0.6,
                "in_degree": 0, "out_degree": 1, "total_degree": 1
            },
            "B": {
                "pagerank": 0.35, "degree_centrality": 0.5,
                "betweenness": 1.0, "closeness": 0.75,
                "in_degree": 1, "out_degree": 1, "total_degree": 2
            },
            "C": {
                "pagerank": 0.25, "degree_centrality": 0.5,
                "betweenness": 0.0, "closeness": 0.6,
                "in_degree": 1, "out_degree": 0, "total_degree": 1
            },
        }
        self.visualizer = NetworkVisualizer(self.graph, self.metrics)

    def test_interactive_network_returns_figure(self):
        """Interactive network returns a Plotly figure."""
        fig = self.visualizer.generate_interactive_network()
        assert fig is not None
        assert hasattr(fig, "data")
        assert len(getattr(fig, "data", ())) > 0

    def test_interactive_network_layout_options(self):
        """Different layout options produce valid figures."""
        spring_fig = self.visualizer.generate_interactive_network(layout="spring")
        assert len(getattr(spring_fig, "data", ())) > 0

        circular_fig = self.visualizer.generate_interactive_network(layout="circular")
        assert len(getattr(circular_fig, "data", ())) > 0

    def test_influence_chart(self):
        """Influence chart returns a Plotly figure with bars."""
        fig = self.visualizer.generate_influence_chart(top_n=3)
        assert fig is not None
        assert len(getattr(fig, "data", ())) > 0

    def test_community_chart_empty(self):
        """Community chart handles empty communities dict."""
        fig = self.visualizer.generate_community_chart({})
        assert fig is not None

    def test_community_chart_with_data(self):
        """Community chart with data returns bar figure."""
        communities = {"A": 0, "B": 1, "C": 1}
        fig = self.visualizer.generate_community_chart(communities)
        assert fig is not None
        assert len(getattr(fig, "data", ())) > 0

    def test_sample_graph_small(self):
        """Small graph under max_nodes returns unchanged."""
        sampled = self.visualizer._sample_graph(max_nodes=10)
        assert sampled.number_of_nodes() == 3

    def test_metric_encoding(self):
        """Node sizing and coloring use metric values."""
        # Degree-based sizing
        fig = self.visualizer.generate_interactive_network(
            color_by="pagerank",
            node_size_metric="in_degree"
        )
        assert fig is not None

        # Betweenness coloring
        fig = self.visualizer.generate_interactive_network(
            color_by="betweenness",
            node_size_metric="total_degree"
        )
        assert fig is not None