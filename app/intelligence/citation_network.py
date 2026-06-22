"""
Citation Network Analysis Module.

Extracts citation relationships from PubMed articles, builds a directed
citation graph, calculates influence metrics, and generates interactive
visualizations for research discovery.

Key capabilities:
- Build citation graphs from PMID lists
- Calculate PageRank, centrality, and influence metrics
- Identify bridge papers and research communities
- Generate interactive Plotly network visualizations
- Export network data in standard formats
"""

import logging
import pickle
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple, Any, cast

import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from Bio import Entrez

from app.config import NCBI_EMAIL, NCBI_API_KEY

# Configure Entrez for PubMed API access
Entrez.email = NCBI_EMAIL
if NCBI_API_KEY:
    Entrez.api_key = NCBI_API_KEY

logger = logging.getLogger(__name__)


class CitationNetworkBuilder:
    """
    Builds and manages citation networks from PubMed articles.

    Orchestrates the full pipeline:
    1. Fetch citation data via Entrez elink
    2. Build directed graph (edges = citations)
    3. Calculate network metrics

    Usage:
        builder = CitationNetworkBuilder()
        graph = builder.build_network(["12345", "67890"])
        stats = builder.get_network_stats()
    """

    def __init__(self):
        """Initialize builder with empty graph and metadata store."""
        self.graph: nx.DiGraph = nx.DiGraph()
        self.metadata: Dict = {}
        self._node_publication_data: Dict[str, Dict] = {}

    def build_network(self, pmids: List[str]) -> nx.DiGraph:
        """
        Build a complete citation network from a list of PMIDs.

        Args:
            pmids: List of PubMed IDs for seed papers.

        Returns:
            NetworkX DiGraph where:
            - Nodes = papers (seed + cited/citing papers discovered)
            - Edge (A → B) = paper A cites paper B
            - Node attributes store citation metadata
        """
        logger.info("Building citation network for %d seed papers", len(pmids))
        self.graph = nx.DiGraph()

        # Add seed papers as primary nodes
        for pmid in set(pmids):
            self.graph.add_node(pmid, seed=True, external=False)

        # Fetch citation data for each seed paper
        for pmid in list(self.graph.nodes()):
            try:
                citations = self._extract_citations_for_paper(pmid)
                self._add_citations_to_graph(pmid, citations)
            except Exception as exc:
                logger.warning("Citation fetch failed for %s: %s", pmid, exc)

        # Attach computed metrics as node attributes
        self._calculate_network_metrics()

        logger.info(
            "Network built: %d nodes, %d edges",
            self.graph.number_of_nodes(),
            self.graph.number_of_edges(),
        )
        return self.graph

    def add_papers(self, pmids: List[str]) -> None:
        """
        Incrementally add new papers to an existing network.

        Useful when expanding a previously built network with
        additional seed papers discovered during analysis.

        Args:
            pmids: New PubMed IDs to add.
        """
        new_pmids = [p for p in pmids if p not in self.graph]
        for pmid in new_pmids:
            self.graph.add_node(pmid, seed=True, external=False)

        for pmid in new_pmids:
            try:
                citations = self._extract_citations_for_paper(pmid)
                self._add_citations_to_graph(pmid, citations)
            except Exception as exc:
                logger.warning("Citation fetch failed for %s: %s", pmid, exc)

        self._calculate_network_metrics()

    def _extract_citations_for_paper(
        self, pmid: str
    ) -> Dict[str, List[str]]:
        """
        Retrieve citation data for a single PubMed article.

        Uses NCBI Entrez elink with two linknames:
        - pubmed_pubmed_refs: papers this article references
        - pubmed_pubmed_citedin: papers that cite this article

        Args:
            pmid: PubMed ID string.

        Returns:
            Dict with keys 'references' and 'cited_by',
            each containing a list of PMID strings.
        """
        result: Dict[str, List[str]] = {"references": [], "cited_by": []}

        # --- Fetch references (papers citing ← this paper cites → references) ---
        try:
            with Entrez.elink(
                dbfrom="pubmed",
                id=pmid,
                linkname="pubmed_pubmed_refs",
            ) as handle:
                refs_record = Entrez.read(handle)

            refs_list = cast(List[Dict[str, Any]], refs_record) if refs_record else []
            if refs_list and refs_list[0].get("LinkSetDb"):
                result["references"] = [
                    link["Id"]
                    for link in refs_list[0]["LinkSetDb"][0].get("Link", [])
                ]
        except Exception as exc:
            logger.debug("References fetch failed for %s: %s", pmid, exc)

        # --- Fetch citations (other papers that cite this paper) ---
        try:
            with Entrez.elink(
                dbfrom="pubmed",
                id=pmid,
                linkname="pubmed_pubmed_citedin",
            ) as handle:
                cites_record = Entrez.read(handle)

            cites_list = cast(List[Dict[str, Any]], cites_record) if cites_record else []
            if cites_list and cites_list[0].get("LinkSetDb"):
                result["cited_by"] = [
                    link["Id"]
                    for link in cites_list[0]["LinkSetDb"][0].get("Link", [])
                ]
        except Exception as exc:
            logger.debug("Cited-by fetch failed for %s: %s", pmid, exc)

        return result

    def _add_citations_to_graph(
        self, pmid: str, citations: Dict[str, List[str]]
    ) -> None:
        """
        Add directed edges to the graph based on citation data.

        Edge direction convention:
        - Source → Target = Source cites Target

        Args:
            pmid: The paper whose citations are being added.
            citations: Dict with 'references' and 'cited_by' PMID lists.
        """
        # This paper cites → references (pmid → ref)
        for cited_pmid in citations.get("references", []):
            if cited_pmid not in self.graph:
                self.graph.add_node(cited_pmid, seed=False, external=True)
            self.graph.add_edge(pmid, cited_pmid, citation_type="reference")

        # Citing papers → this paper (citing → pmid)
        for citing_pmid in citations.get("cited_by", []):
            if citing_pmid not in self.graph:
                self.graph.add_node(citing_pmid, seed=False, external=True)
            self.graph.add_edge(citing_pmid, pmid, citation_type="citation")

    def _calculate_network_metrics(self) -> None:
        """Compute summary statistics for the current network state."""
        n_nodes = self.graph.number_of_nodes()
        n_edges = self.graph.number_of_edges()
        self.metadata["num_nodes"] = n_nodes
        self.metadata["num_edges"] = n_edges
        self.metadata["density"] = nx.density(self.graph) if n_nodes > 0 else 0.0

        if n_nodes == 0:
            return

        # Connected-components analysis
        undirected = self.graph.to_undirected()
        if nx.is_connected(undirected):
            self.metadata["is_connected"] = True
            try:
                self.metadata["diameter"] = nx.diameter(undirected)
            except nx.NetworkXError:
                self.metadata["diameter"] = float("inf")
        else:
            self.metadata["is_connected"] = False
            components = list(nx.connected_components(undirected))
            if components:
                largest = max(components, key=len)
                self.metadata["largest_component_size"] = len(largest)
                self.metadata["num_components"] = len(components)

        # Clustering coefficient
        if n_nodes > 1:
            self.metadata["clustering_coefficient"] = (
                nx.average_clustering(undirected)
            )
        else:
            self.metadata["clustering_coefficient"] = 0.0

    def get_network_stats(self) -> Dict:
        """Return a human-readable summary of current network statistics."""
        return {
            "Papers in network": self.metadata.get("num_nodes", 0),
            "Citation links": self.metadata.get("num_edges", 0),
            "Network density": f"{self.metadata.get('density', 0.0):.4f}",
            "Connected": self.metadata.get("is_connected", False),
            "Largest component": self.metadata.get(
                "largest_component_size", "N/A"
            ),
            "Clustering coefficient": f"{self.metadata.get('clustering_coefficient', 0.0):.4f}",
        }


class NetworkAnalyzer:
    """
    Calculates influence and importance metrics for citation networks.

    Metrics computed:
    - PageRank: influence propagation through citation chains
    - Degree centrality: raw citation counts (normalized)
    - Betweenness centrality: bridge/connector papers
    - Closeness centrality: proximity to all other papers
    - Community detection: Louvain algorithm for research clusters
    """

    def __init__(self, graph: nx.DiGraph):
        """
        Args:
            graph: A NetworkX DiGraph representing the citation network.
        """
        self.graph = graph
        self.metrics: Dict[str, Dict[str, float]] = {}

    def calculate_all_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Compute all influence metrics and cache them.

        Returns:
            Dict mapping each PMID to its metrics:
            {
                "12345": {
                    "pagerank": 0.042,
                    "degree_centrality": 0.15,
                    "betweenness": 0.08,
                    "closeness": 0.31,
                    "in_degree": 12,
                    "out_degree": 8,
                    "total_degree": 20
                },
                ...
            }
        """
        logger.info("Calculating all influence metrics")
        if self.graph.number_of_nodes() == 0:
            return {}

        pagerank = self.calculate_pagerank()
        degree_cent = self.calculate_degree_centrality()
        betweenness = self.calculate_betweenness_centrality()
        closeness = self.calculate_closeness_centrality()

        self.metrics = {}
        for node in self.graph.nodes():
            self.metrics[node] = {
                "pagerank": pagerank.get(node, 0.0),
                "degree_centrality": degree_cent.get(node, 0.0),
                "betweenness": betweenness.get(node, 0.0),
                "closeness": closeness.get(node, 0.0),
                "in_degree": int(self.graph.in_degree(node)),
                "out_degree": int(self.graph.out_degree(node)),
                "total_degree": int(self.graph.degree(node)),
            }

        return self.metrics

    def calculate_pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        """
        PageRank algorithm for citation influence.

        Papers cited by many important papers receive higher scores.
        The damping factor alpha represents the probability of following
        a citation link vs. jumping to a random paper.

        Args:
            alpha: Damping parameter (default 0.85).

        Returns:
            Dict mapping PMID → PageRank score (sums to 1.0).
        """
        try:
            return nx.pagerank(self.graph, alpha=alpha)
        except Exception as exc:
            logger.error("PageRank calculation failed: %s", exc)
            return {}

    def calculate_degree_centrality(self) -> Dict[str, float]:
        """
        Normalized degree centrality.

        High in-degree = highly cited (authoritative).
        High out-degree = cites many others (hub).

        Returns:
            Dict mapping PMID → degree centrality [0, 1].
        """
        return nx.degree_centrality(self.graph)

    def calculate_betweenness_centrality(self) -> Dict[str, float]:
        """
        Betweenness centrality to identify bridge papers.

        Papers with high betweenness sit on citation paths between
        different research communities. For large networks (>1000 nodes),
        uses approximation sampling for performance.

        Returns:
            Dict mapping PMID → betweenness centrality [0, 1].
        """
        try:
            n = self.graph.number_of_nodes()
            if n > 1000:
                k = max(100, n // 10)
                return nx.betweenness_centrality(self.graph, k=k)
            return nx.betweenness_centrality(self.graph)
        except Exception as exc:
            logger.error("Betweenness calculation failed: %s", exc)
            return {}

    def calculate_closeness_centrality(self) -> Dict[str, float]:
        """
        Closeness centrality measuring proximity to all other papers.

        High closeness = paper is centrally positioned in the research field.
        Lower values indicate peripheral/specialized papers.

        Returns:
            Dict mapping PMID → closeness centrality [0, 1].
        """
        try:
            return nx.closeness_centrality(self.graph)
        except Exception as exc:
            logger.error("Closeness calculation failed: %s", exc)
            return {}

    def identify_influential_papers(
        self, top_n: int = 20
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Rank papers by each influence metric and return top candidates.

        Args:
            top_n: Number of top papers per category.

        Returns:
            Dict with keys for each ranking type:
            - "pagerank": top papers by PageRank
            - "most_cited": top papers by citation count
            - "bridges": top papers by betweenness centrality
            - "central": top papers by closeness centrality
        """
        if not self.metrics:
            self.calculate_all_metrics()

        influential: Dict[str, List[Tuple[str, float]]] = {}

        # Top by PageRank
        influential["pagerank"] = sorted(
            [
                (pmid, m["pagerank"])
                for pmid, m in self.metrics.items()
            ],
            key=lambda x: x[1],
            reverse=True,
        )[:top_n]

        # Most cited (by in-degree)
        influential["most_cited"] = sorted(
            [
                (pmid, m["in_degree"])
                for pmid, m in self.metrics.items()
            ],
            key=lambda x: x[1],
            reverse=True,
        )[:top_n]

        # Bridge papers (by betweenness)
        influential["bridges"] = sorted(
            [
                (pmid, m["betweenness"])
                for pmid, m in self.metrics.items()
            ],
            key=lambda x: x[1],
            reverse=True,
        )[:top_n]

        # Central papers (by closeness)
        influential["central"] = sorted(
            [
                (pmid, m["closeness"])
                for pmid, m in self.metrics.items()
            ],
            key=lambda x: x[1],
            reverse=True,
        )[:top_n]

        return influential

    def detect_communities(
        self, seed: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Detect research communities using the Louvain algorithm.

        Groups papers into densely connected clusters representing
        distinct research areas or subtopics.

        Args:
            seed: Random seed for reproducibility.

        Returns:
            Dict mapping PMID → community ID (integer).
            Returns empty dict if python-louvain is not installed.
        """
        try:
            import community as community_louvain

            undirected = self.graph.to_undirected()
            communities = community_louvain.best_partition(
                undirected, random_state=seed
            )

            n_communities = len(set(communities.values()))
            logger.info("Detected %d research communities", n_communities)
            return communities

        except ImportError:
            logger.warning(
                "python-louvain not installed. "
                "Install with: pip install python-louvain"
            )
            return {}
        except Exception as exc:
            logger.error("Community detection failed: %s", exc)
            return {}

    def summarize(self) -> pd.DataFrame:
        """
        Produce a summary DataFrame of all metrics.

        Useful for exporting to CSV or displaying in dashboards.

        Returns:
            DataFrame with columns: pmid, pagerank, degree_centrality,
            betweenness, closeness, in_degree, out_degree, total_degree.
        """
        if not self.metrics:
            self.calculate_all_metrics()

        rows = []
        for pmid, m in self.metrics.items():
            rows.append(
                {
                    "pmid": pmid,
                    "pagerank": m["pagerank"],
                    "degree_centrality": m["degree_centrality"],
                    "betweenness": m["betweenness"],
                    "closeness": m["closeness"],
                    "in_degree": m["in_degree"],
                    "out_degree": m["out_degree"],
                    "total_degree": m["total_degree"],
                }
            )

        return pd.DataFrame(rows).sort_values(
            "pagerank", ascending=False
        )


class NetworkVisualizer:
    """
    Generates interactive visualizations of citation networks.

    Produces Plotly figures with:
    - Force-directed node layouts (spring, Kamada-Kawai, circular)
    - Node sizing by citation count
    - Node coloring by PageRank or community
    - Interactive hover tooltips with metrics
    - Performance sampling for large networks
    """

    def __init__(self, graph: nx.DiGraph, metrics: Dict[str, Dict]):
        """
        Args:
            graph: NetworkX DiGraph of citations.
            metrics: Dict from NetworkAnalyzer with per-node metrics.
        """
        self.graph = graph
        self.metrics = metrics

    def generate_interactive_network(
        self,
        layout: str = "spring",
        max_nodes: int = 200,
        color_by: str = "pagerank",
        node_size_metric: str = "in_degree",
    ) -> go.Figure:
        """
        Create an interactive Plotly network visualization.

        Args:
            layout: Layout algorithm.
                Options: "spring", "kamada_kawai", "circular".
            max_nodes: Maximum nodes to plot (filters to most central).
            color_by: Metric for node coloring.
                Options: "pagerank", "betweenness", "closeness".
            node_size_metric: Metric for node sizing.
                Options: "in_degree", "total_degree", "pagerank".

        Returns:
            Plotly Figure with interactive network graph.
        """
        # Sample nodes if network is too large
        subgraph = self._sample_graph(max_nodes)
        pos = self._compute_layout(subgraph, layout)

        # Build traces
        edge_trace = self._create_edge_trace(subgraph, pos)
        node_trace = self._create_node_trace(
            subgraph, pos, color_by, node_size_metric
        )

        # Assemble figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title={"text": "Citation Network", "font": {"size": 16}},
                showlegend=False,
                hovermode="closest",
                margin={"b": 20, "l": 20, "r": 20, "t": 50},
                xaxis={
                    "showgrid": False,
                    "zeroline": False,
                    "showticklabels": False,
                },
                yaxis={
                    "showgrid": False,
                    "zeroline": False,
                    "showticklabels": False,
                },
                height=800,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            ),
        )

        return fig

    def _sample_graph(self, max_nodes: int) -> nx.DiGraph:
        """Sample top-N nodes by a composite importance score."""
        if self.graph.number_of_nodes() <= max_nodes:
            return self.graph

        # Composite score: PageRank + normalized degree
        scores = {}
        for node in self.graph.nodes():
            m = self.metrics.get(node, {})
            pr = m.get("pagerank", 0.0)
            deg = m.get("total_degree", 0)
            # Normalize degree by max degree in graph
            max_deg = max(
                (self.metrics.get(n, {}).get("total_degree", 0))
                for n in self.graph.nodes()
            )
            deg_norm = deg / max_deg if max_deg > 0 else 0
            scores[node] = pr + deg_norm

        top_nodes = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)[:max_nodes]
        return self.graph.subgraph(top_nodes).copy()

    def _compute_layout(
        self, subgraph: nx.DiGraph, layout: str
    ) -> Dict[str, np.ndarray]:
        """Compute 2D positions for nodes using the chosen layout."""
        if layout == "spring":
            return nx.spring_layout(
                subgraph, k=0.5, iterations=50, seed=42
            )
        elif layout == "kamada_kawai":
            return nx.kamada_kawai_layout(subgraph)
        else:
            return nx.circular_layout(subgraph)

    def _create_edge_trace(
        self, subgraph: nx.DiGraph, pos: Dict
    ) -> go.Scatter:
        """Build a line-scatter trace for graph edges."""
        edge_x, edge_y = [], []
        for u, v in subgraph.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        return go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line={"width": 0.5, "color": "#888", "simplify": True},
            hoverinfo="none",
        )

    def _create_node_trace(
        self,
        subgraph: nx.DiGraph,
        pos: Dict,
        color_by: str,
        size_by: str,
    ) -> go.Scatter:
        """Build a scatter trace for nodes with encoding by metrics."""
        node_x, node_y = [], []
        node_text, node_size, node_color = [], [], []

        for node in subgraph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            m = self.metrics.get(node, {})
            color_val = m.get(color_by, 0.0)
            size_val = m.get(size_by, 5)

            # Size range: 5-40 px
            if size_by in ("in_degree", "total_degree", "out_degree"):
                max_deg = max(
                    self.metrics.get(n, {}).get(size_by, 0)
                    for n in subgraph.nodes()
                )
                size_val = (
                    max(5, min(40, size_val * 40 / max_deg))
                    if max_deg > 0
                    else 10
                )
            else:
                size_val = max(5, min(40, size_val * 500))

            node_size.append(size_val)
            node_color.append(color_val)

            # Hover tooltip
            node_text.append(
                f"<b>PMID</b>: {node}<br>"
                f"<b>Citations</b>: {m.get('in_degree', 0)}<br>"
                f"<b>References</b>: {m.get('out_degree', 0)}<br>"
                f"<b>PageRank</b>: {m.get('pagerank', 0):.5f}<br>"
                f"<b>Betweenness</b>: {m.get('betweenness', 0):.5f}<br>"
                f"<b>Closeness</b>: {m.get('closeness', 0):.5f}"
            )

        return go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers",
            hoverinfo="text",
            text=node_text,
            marker={
                "showscale": True,
                "colorscale": "Viridis",
                "size": node_size,
                "color": node_color,
                "colorbar": {
                    "title": {
                        "text": color_by.replace("_", " ").title(),
                        "side": "right"
                    },
                    "xanchor": "left",
                },
                "line": {"width": 1, "color": "#FFF"},
                "sizemode": "area",
            },
        )

    def generate_influence_chart(
        self, top_n: int = 20
    ) -> go.Figure:
        """Generate a horizontal bar chart of top papers by PageRank."""
        if not self.metrics:
            return go.Figure()

        sorted_papers = sorted(
            self.metrics.items(),
            key=lambda x: x[1].get("pagerank", 0),
            reverse=True,
        )[:top_n]

        pmids = [p[0][:40] + "…" if len(p[0]) > 40 else p[0] for p in sorted_papers]
        pageranks = [p[1].get("pagerank", 0) for p in sorted_papers]
        citations = [p[1].get("in_degree", 0) for p in sorted_papers]

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=pmids[::-1],
                x=pageranks[::-1],
                orientation="h",
                name="PageRank",
                marker={"color": pageranks[::-1], "colorscale": "Viridis"},
                text=[f"Cited {c} times" for c in citations[::-1]],
                hovertemplate="%{y}<br>PageRank: %{x:.5f}<br>%{text}<extra></extra>",
            )
        )

        fig.update_layout(
            title="Most Influential Papers (by PageRank)",
            xaxis={"title": "PageRank Score"},
            yaxis={"title": ""},
            height=max(400, top_n * 20),
            margin={"l": 150, "r": 20, "t": 50, "b": 20},
        )

        return fig

    def generate_community_chart(
        self, communities: Dict[str, int]
    ) -> go.Figure:
        """
        Generate a bar chart showing community sizes.

        Args:
            communities: Dict from NetworkAnalyzer.detect_communities()
                mapping PMID → community ID.

        Returns:
            Plotly bar chart figure.
        """
        if not communities:
            return go.Figure()

        counts = defaultdict(int)
        for cid in communities.values():
            counts[cid] += 1

        community_ids = list(counts.keys())
        sizes = [counts[cid] for cid in community_ids]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=[f"Community {cid}" for cid in community_ids],
                    y=sizes,
                    marker={"colorscale": "Viridis", "color": sizes},
                    text=sizes,
                    textposition="auto",
                )
            ]
        )

        fig.update_layout(
            title="Research Communities (Louvain Detection)",
            xaxis={"title": "Community"},
            yaxis={"title": "Number of Papers"},
            height=400,
        )

        return fig