# PHASE 1: CITATION NETWORK ANALYSIS
## Detailed Technical Specification

**Priority**: CRITICAL (Highest ROI)  
**Effort**: 16-24 hours  
**Portfolio Impact**: +2.0 points  
**Dependencies**: None (foundational feature)  
**Status**: Ready for implementation

---

## OVERVIEW

Transform the project from a simple literature search tool into a research intelligence platform by adding citation network analysis. This feature will:
- Extract citation relationships between papers
- Build directed graph of citations
- Calculate influence metrics (PageRank, centrality, etc.)
- Identify key papers, bridges, and communities
- Provide interactive network visualizations
- Enable citation-based discovery

---

## TECHNICAL ARCHITECTURE

### Module Structure
```
app/intelligence/citation_network.py
├── CitationNetworkBuilder
│   ├── build_network()
│   ├── extract_citations()
│   └── enrich_metadata()
├── NetworkAnalyzer
│   ├── calculate_centrality()
│   ├── identify_influential_papers()
│   └── detect_communities()
├── NetworkVisualizer
│   ├── generate_network_graph()
│   ├── create_influence_chart()
│   └── export_network_data()
└── CitationSearchEngine
    ├── find_citing_papers()
    ├── find_cited_papers()
    └── get_citation_path()
```

---

## DATA MODEL

### Citation Relationship
```python
class Citation:
    citing_pmid: str        # Paper that cites
    cited_pmid: str         # Paper being cited
    citation_context: str   # Optional: where citation appears
    confidence: float       # Citation extraction confidence
    discovered_at: datetime
```

### Extended Article Model
```python
class Article:
    # Existing fields
    pmid: str
    title: str
    authors: List[str]
    journal: str
    pub_date: str
    abstract: str
    doi: str
    
    # NEW citation fields
    citations_out: List[str]      # Papers this cites
    citations_in: List[str]       # Papers citing this
    citation_count: int           # Number of times cited
    reference_count: int          # Number of references
    
    # NEW influence metrics
    pagerank_score: float
    betweenness_centrality: float
    degree_centrality: float
    closeness_centrality: float
    
    # NEW derived fields
    is_highly_cited: bool         # Top 10% by citations
    is_bridge_paper: bool         # High betweenness
    community_id: int             # Research community
```

### Network Statistics
```python
class NetworkStats:
    total_papers: int
    total_citations: int
    avg_citations_per_paper: float
    network_density: float
    num_communities: int
    largest_component_size: int
    avg_path_length: float
    clustering_coefficient: float
```

---

## IMPLEMENTATION SPECIFICATION

### 1. Citation Extraction from PubMed

**File**: `app/intelligence/citation_network.py`

```python
"""
Citation Network Analysis Module.

This module extracts citation relationships from PubMed articles and builds
a directed citation graph for influence analysis and research discovery.
"""

import networkx as nx
from typing import List, Dict, Set, Tuple, Optional
import pandas as pd
from collections import defaultdict
import logging
from Bio import Entrez
from app.config import NCBI_EMAIL, NCBI_API_KEY

logger = logging.getLogger(__name__)


class CitationNetworkBuilder:
    """Builds citation networks from PubMed articles."""
    
    def __init__(self):
        """Initialize citation network builder."""
        self.graph = nx.DiGraph()
        self.metadata = {}
        
    def build_network(self, pmids: List[str]) -> nx.DiGraph:
        """
        Build citation network from list of PMIDs.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            NetworkX directed graph where edges represent citations
        """
        logger.info(f"Building citation network for {len(pmids)} papers")
        
        # Step 1: Add all papers as nodes
        for pmid in pmids:
            self.graph.add_node(pmid)
            
        # Step 2: Extract citations for each paper
        for pmid in pmids:
            try:
                citations = self._extract_citations_for_paper(pmid)
                self._add_citations_to_graph(pmid, citations)
            except Exception as e:
                logger.error(f"Failed to extract citations for {pmid}: {e}")
                
        # Step 3: Calculate network metrics
        self._calculate_network_metrics()
        
        logger.info(
            f"Network built: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges"
        )
        
        return self.graph
        
    def _extract_citations_for_paper(self, pmid: str) -> Dict[str, List[str]]:
        """
        Extract citation data for a single paper.
        
        Args:
            pmid: PubMed ID
            
        Returns:
            Dictionary with 'references' and 'cited_by' lists
        """
        # Use Entrez elink to get citation data
        try:
            # Get papers this paper references
            handle_refs = Entrez.elink(
                dbfrom="pubmed",
                id=pmid,
                linkname="pubmed_pubmed_refs"
            )
            refs_record = Entrez.read(handle_refs)
            handle_refs.close()
            
            references = []
            if refs_record[0]["LinkSetDb"]:
                references = [
                    link["Id"] 
                    for link in refs_record[0]["LinkSetDb"][0]["Link"]
                ]
            
            # Get papers that cite this paper
            handle_cites = Entrez.elink(
                dbfrom="pubmed",
                id=pmid,
                linkname="pubmed_pubmed_citedin"
            )
            cites_record = Entrez.read(handle_cites)
            handle_cites.close()
            
            cited_by = []
            if cites_record[0]["LinkSetDb"]:
                cited_by = [
                    link["Id"]
                    for link in cites_record[0]["LinkSetDb"][0]["Link"]
                ]
            
            return {
                "references": references,
                "cited_by": cited_by
            }
            
        except Exception as e:
            logger.error(f"Citation extraction failed for {pmid}: {e}")
            return {"references": [], "cited_by": []}
            
    def _add_citations_to_graph(
        self, 
        pmid: str, 
        citations: Dict[str, List[str]]
    ):
        """Add citation edges to graph."""
        # Add edges for references (pmid cites these)
        for cited_pmid in citations["references"]:
            # Add cited paper as node if not in original set
            if cited_pmid not in self.graph:
                self.graph.add_node(cited_pmid, external=True)
            self.graph.add_edge(pmid, cited_pmid, type="cites")
            
        # Add edges for citations (these cite pmid)
        for citing_pmid in citations["cited_by"]:
            if citing_pmid not in self.graph:
                self.graph.add_node(citing_pmid, external=True)
            self.graph.add_edge(citing_pmid, pmid, type="cites")
            
    def _calculate_network_metrics(self):
        """Calculate and store network-level metrics."""
        if self.graph.number_of_nodes() == 0:
            return
            
        # Basic metrics
        self.metadata["num_nodes"] = self.graph.number_of_nodes()
        self.metadata["num_edges"] = self.graph.number_of_edges()
        self.metadata["density"] = nx.density(self.graph)
        
        # Connected components
        if nx.is_weakly_connected(self.graph):
            self.metadata["is_connected"] = True
            self.metadata["diameter"] = nx.diameter(self.graph.to_undirected())
        else:
            self.metadata["is_connected"] = False
            largest_cc = max(
                nx.weakly_connected_components(self.graph), 
                key=len
            )
            self.metadata["largest_component_size"] = len(largest_cc)
        
        # Clustering
        self.metadata["clustering_coefficient"] = nx.average_clustering(
            self.graph.to_undirected()
        )
```

### 2. Influence Metrics Calculator

```python
class NetworkAnalyzer:
    """Analyzes citation networks for influence and importance."""
    
    def __init__(self, graph: nx.DiGraph):
        """Initialize network analyzer."""
        self.graph = graph
        self.metrics = {}
        
    def calculate_all_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate all influence metrics for each node.
        
        Returns:
            Dictionary mapping PMID to metrics dict
        """
        logger.info("Calculating influence metrics")
        
        metrics = {}
        
        # PageRank - most important metric
        pagerank = self.calculate_pagerank()
        
        # Centrality measures
        degree_cent = self.calculate_degree_centrality()
        betweenness = self.calculate_betweenness_centrality()
        closeness = self.calculate_closeness_centrality()
        
        # Combine all metrics
        for node in self.graph.nodes():
            metrics[node] = {
                "pagerank": pagerank.get(node, 0.0),
                "degree_centrality": degree_cent.get(node, 0.0),
                "betweenness": betweenness.get(node, 0.0),
                "closeness": closeness.get(node, 0.0),
                "in_degree": self.graph.in_degree(node),
                "out_degree": self.graph.out_degree(node),
                "total_degree": self.graph.degree(node)
            }
        
        self.metrics = metrics
        return metrics
        
    def calculate_pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        """
        Calculate PageRank for all nodes.
        
        PageRank identifies the most influential papers based on
        citation patterns. Papers cited by important papers get
        higher scores.
        
        Args:
            alpha: Damping parameter (default 0.85)
            
        Returns:
            Dictionary mapping PMID to PageRank score
        """
        try:
            return nx.pagerank(self.graph, alpha=alpha)
        except Exception as e:
            logger.error(f"PageRank calculation failed: {e}")
            return {}
            
    def calculate_degree_centrality(self) -> Dict[str, float]:
        """
        Calculate degree centrality (normalized).
        
        Measures how connected a paper is. High in-degree means
        highly cited. High out-degree means cites many others.
        """
        return nx.degree_centrality(self.graph)
        
    def calculate_betweenness_centrality(self) -> Dict[str, float]:
        """
        Calculate betweenness centrality.
        
        Identifies "bridge" papers that connect different research
        areas. High betweenness means the paper is on paths between
        many other papers.
        """
        try:
            # This can be slow for large graphs - use sampling
            if self.graph.number_of_nodes() > 1000:
                # Sample-based approximation
                k = min(100, self.graph.number_of_nodes() // 10)
                return nx.betweenness_centrality(self.graph, k=k)
            else:
                return nx.betweenness_centrality(self.graph)
        except Exception as e:
            logger.error(f"Betweenness calculation failed: {e}")
            return {}
            
    def calculate_closeness_centrality(self) -> Dict[str, float]:
        """
        Calculate closeness centrality.
        
        Measures how close a paper is to all other papers in the
        network. High closeness means the paper is central to the
        research field.
        """
        try:
            return nx.closeness_centrality(self.graph)
        except Exception as e:
            logger.error(f"Closeness calculation failed: {e}")
            return {}
            
    def identify_influential_papers(
        self, 
        top_n: int = 20
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Identify most influential papers by various metrics.
        
        Args:
            top_n: Number of top papers to return per metric
            
        Returns:
            Dictionary with lists of (PMID, score) tuples
        """
        if not self.metrics:
            self.calculate_all_metrics()
            
        influential = {}
        
        # Top by PageRank
        influential["pagerank"] = sorted(
            [(pmid, m["pagerank"]) for pmid, m in self.metrics.items()],
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        # Most cited
        influential["most_cited"] = sorted(
            [(pmid, m["in_degree"]) for pmid, m in self.metrics.items()],
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        # Bridge papers
        influential["bridges"] = sorted(
            [(pmid, m["betweenness"]) for pmid, m in self.metrics.items()],
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        # Central papers
        influential["central"] = sorted(
            [(pmid, m["closeness"]) for pmid, m in self.metrics.items()],
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return influential
        
    def detect_communities(self) -> Dict[str, int]:
        """
        Detect research communities using Louvain algorithm.
        
        Returns:
            Dictionary mapping PMID to community ID
        """
        try:
            import community as community_louvain
            
            # Convert to undirected for community detection
            undirected = self.graph.to_undirected()
            
            # Apply Louvain algorithm
            communities = community_louvain.best_partition(undirected)
            
            logger.info(f"Detected {len(set(communities.values()))} communities")
            
            return communities
            
        except ImportError:
            logger.warning(
                "python-louvain not installed. "
                "Install with: pip install python-louvain"
            )
            return {}
        except Exception as e:
            logger.error(f"Community detection failed: {e}")
            return {}
```

---

## VISUALIZATION SPECIFICATION

### Interactive Network Graph with Plotly

```python
class NetworkVisualizer:
    """Creates interactive visualizations of citation networks."""
    
    def __init__(self, graph: nx.DiGraph, metrics: Dict):
        """Initialize visualizer."""
        self.graph = graph
        self.metrics = metrics
        
    def generate_interactive_network(
        self,
        layout: str = "spring",
        max_nodes: int = 200
    ) -> go.Figure:
        """
        Generate interactive network visualization.
        
        Args:
            layout: Layout algorithm ("spring", "kamada_kawai", "circular")
            max_nodes: Maximum nodes to display (for performance)
            
        Returns:
            Plotly Figure object
        """
        import plotly.graph_objects as go
        
        # Sample nodes if too many
        if self.graph.number_of_nodes() > max_nodes:
            # Keep most influential nodes
            top_nodes = self._get_top_nodes(max_nodes)
            subgraph = self.graph.subgraph(top_nodes)
        else:
            subgraph = self.graph
            
        # Calculate layout positions
        if layout == "spring":
            pos = nx.spring_layout(subgraph, k=0.5, iterations=50)
        elif layout == "kamada_kawai":
            pos = nx.kamada_kawai_layout(subgraph)
        else:
            pos = nx.circular_layout(subgraph)
            
        # Create edge traces
        edge_trace = self._create_edge_trace(subgraph, pos)
        
        # Create node traces
        node_trace = self._create_node_trace(subgraph, pos)
        
        # Create figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title="Citation Network",
                showlegend=False,
                hovermode="closest",
                margin=dict(b=0, l=0, r=0, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=800
            )
        )
        
        return fig
        
    def _create_edge_trace(self, graph, pos):
        """Create edge trace for network graph."""
        edge_x = []
        edge_y = []
        
        for edge in graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
        return go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=0.5, color="#888"),
            hoverinfo="none",
            mode="lines"
        )
        
    def _create_node_trace(self, graph, pos):
        """Create node trace with hover info."""
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        node_color = []
        
        for node in graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Get metrics
            metrics = self.metrics.get(node, {})
            pagerank = metrics.get("pagerank", 0)
            citations = metrics.get("in_degree", 0)
            
            # Node size based on citations
            node_size.append(max(5, min(40, citations * 2)))
            
            # Color based on PageRank
            node_color.append(pagerank)
            
            # Hover text
            node_text.append(
                f"PMID: {node}<br>"
                f"Citations: {citations}<br>"
                f"PageRank: {pagerank:.4f}"
            )
            
        return go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers",
            hoverinfo="text",
            text=node_text,
            marker=dict(
                showscale=True,
                colorscale="YlOrRd",
                size=node_size,
                color=node_color,
                colorbar=dict(
                    title="PageRank",
                    xanchor="left",
                    titleside="right"
                ),
                line=dict(width=1, color="#FFF")
            )
        )
```

---

## INTEGRATION WITH EXISTING CODE

### 1. Enhance fetch.py

Add citation extraction to article fetching:

```python
# In app/fetch.py - add to _parse_article()

def _extract_citations(article_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Extract citation PMIDs if available."""
    # This is a placeholder - full implementation in citation_network.py
    return {
        "references": [],
        "cited_by": []
    }
```

### 2. Enhance export.py

Add citation network export:

```python
# In app/export.py

def export_citation_network(
    graph: nx.DiGraph,
    filename: str = "citation_network.graphml"
) -> str:
    """Export citation network in GraphML format."""
    filepath = EXPORTS_DIR / filename
    nx.write_graphml(graph, filepath)
    return str(filepath)
```

### 3. Dashboard Integration

Add new tab in streamlit_app.py:

```python
# In dashboard/streamlit_app.py

with tabs[X]:  # Citation Network tab
    display_citation_network()
```

---

## TESTING STRATEGY

### Unit Tests

```python
# tests/test_intelligence/test_citation_network.py

def test_citation_extraction():
    """Test citation extraction from PubMed."""
    builder = CitationNetworkBuilder()
    citations = builder._extract_citations_for_paper("12345678")
    assert "references" in citations
    assert "cited_by" in citations

def test_pagerank_calculation():
    """Test PageRank on simple graph."""
    G = nx.DiGraph()
    G.add_edges_from([(1, 2), (2, 3), (3, 1)])
    analyzer = NetworkAnalyzer(G)
    pagerank = analyzer.calculate_pagerank()
    assert len(pagerank) == 3
    assert all(0 <= v <= 1 for v in pagerank.values())

def test_community_detection():
    """Test community detection."""
    # Create graph with clear communities
    G = nx.DiGraph()
    # Community 1
    G.add_edges_from([(1, 2), (2, 3), (3, 1)])
    # Community 2
    G.add_edges_from([(4, 5), (5, 6), (6, 4)])
    # Bridge
    G.add_edge(3, 4)
    
    analyzer = NetworkAnalyzer(G)
    communities = analyzer.detect_communities()
    assert len(set(communities.values())) == 2
```

---

## DOCUMENTATION REQUIREMENTS

1. **User Guide**: How to interpret citation metrics
2. **API Reference**: All public methods documented
3. **Examples**: Jupyter notebook with citation analysis
4. **Performance Notes**: Scalability limits and optimizations

---

## SUCCESS CRITERIA

- [ ] Extract citations for 100+ papers in < 2 minutes
- [ ] Calculate PageRank for 500 papers in < 5 seconds
- [ ] Interactive visualization renders smoothly
- [ ] Identify top 20 influential papers correctly
- [ ] Detect research communities with > 0.7 modularity
- [ ] Unit test coverage > 80%
- [ ] Integration tests pass

---

## IMPLEMENTATION CHECKLIST

### Week 1: Core Implementation
- [ ] Create `app/intelligence/citation_network.py`
- [ ] Implement `CitationNetworkBuilder`
- [ ] Implement `NetworkAnalyzer`
- [ ] Add PageRank calculation
- [ ] Add centrality metrics

### Week 2: Visualization & Integration
- [ ] Implement `NetworkVisualizer`
- [ ] Create interactive Plotly graph
- [ ] Integrate with dashboard
- [ ] Add export functionality
- [ ] Write unit tests

### Week 3: Polish & Documentation
- [ ] Optimize performance
- [ ] Add community detection
- [ ] Write integration tests
- [ ] Create Jupyter notebook example
- [ ] Write documentation

---

## NEXT PHASE PREPARATION

This phase sets up the foundation for:
- **Phase 2**: Semantic search (use citation patterns)
- **Phase 3**: Topic modeling (topics per citation community)
- **Phase 4**: Trend detection (citation velocity)

**Estimated completion**: 2-3 weeks part-time

Ready to proceed with implementation?