# Phase 5: Author Collaboration Intelligence Specification

## Overview
Implements network analysis of author collaborations, detecting communities of researchers and identifying influential figures in the field. This demonstrates social network analysis and community detection algorithms—key competencies for bioinformatics roles.

## 1. Directory Structure
```
app/
├── intelligence/
│   ├── author_network.py   # New module
```

## 2. Module Specifications

### `app/intelligence/author_network.py`
**Class: `AuthorNetworkBuilder`**
- `__init__()`: Initializes graph structure.
- `build_network(df: pd.DataFrame) -> nx.Graph`:
  1. Creates nodes for each unique author.
  2. Adds edges between co-authors (weight = number of shared papers).
  3. Returns an undirected graph.

**Class: `AuthorAnalyzer`**
- `__init__(graph: nx.Graph)`: Initializes with author graph.
- `get_top_authors() -> List[Tuple[str, int]]`: Returns authors sorted by number of publications/collaborations.
- `detect_research_groups() -> List[Set[str]]`: Uses community detection (Louvain) to identify research clusters.
- `get_author_stats(author_name: str) -> Dict`: Returns publication count, collaboration count, h-index approximation.
- `find_collaboration_path(author1: str, author2: str) -> List[str]`: Returns shortest path connecting two authors.

## 3. Dashboard Integration
In `dashboard/streamlit_app.py`:
- Add a new tab: "👥 Author Networks".
- Display:
  - Interactive author collaboration graph
  - Top authors ranked by degree/betweenness
  - Research groups/communities
  - Author search tool with path finder

## 4. Testing Strategy
- `tests/test_intelligence/test_author_network.py`
- Create mock data with known authorship patterns.
- Assert community detection correctly clusters co-authors.
- Verify path-finding algorithm.

## 5. Implementation Steps
1. Create `AuthorNetworkBuilder` and `AuthorAnalyzer` using networkx.
2. Integrate community detection (python-louvain or networkx built-ins).
3. Write unit tests.
4. Integrate into Streamlit UI.
5. Verify visualization.
