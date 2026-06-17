# RESEARCH INTELLIGENCE PLATFORM: COMPLETE IMPLEMENTATION GUIDE

**Document Version**: 1.0  
**Last Updated**: June 17, 2026  
**Status**: Ready for Development

---

## QUICK REFERENCE

| Phase | Priority | Hours | Portfolio Impact | Status |
|-------|----------|-------|------------------|--------|
| 1. Citation Networks | CRITICAL | 16-24 | +2.0 pts | Spec Complete ✅ |
| 2. Semantic Search | CRITICAL | 20-28 | +1.5 pts | Spec Below ⬇️ |
| 3. Topic Modeling | CRITICAL | 16-24 | +2.0 pts | Spec Below ⬇️ |
| 4. Trend Detection | HIGH | 12-16 | +1.5 pts | Brief Below |
| 5. Author Networks | MEDIUM | 12-16 | +1.0 pts | Brief Below |
| 6. AI Assistant | MEDIUM | 16-20 | +1.0 pts | Brief Below |
| 7. Production Infra | HIGH | 24-32 | +1.0 pts | Brief Below |

**Total Minimum (Phases 1-3)**: 52-76 hours → Portfolio 8.5/10  
**Total Recommended (All Phases)**: 160-240 hours → Portfolio 9.0/10

---

## PHASE 2: SEMANTIC SEARCH ENGINE

### Overview
Replace keyword-only search with semantic understanding using sentence transformers and vector similarity.

### Technical Stack
- **Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dim, fast)
- **Vector DB**: FAISS (CPU initially, GPU optional)
- **Similarity**: Cosine similarity
- **Cache**: Redis for embeddings

### Implementation Plan

#### 2.1 Embedding Generation Module

**File**: `app/intelligence/semantic_search.py`

```python
"""Semantic search using sentence transformers and vector similarity."""

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List, Dict, Tuple
import pickle
import logging

logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """Semantic search engine using embeddings."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize semantic search engine."""
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.pmid_mapping = {}
        self.embeddings_cache = {}
        
    def build_index(self, articles_df: pd.DataFrame) -> None:
        """
        Build FAISS index from articles.
        
        Args:
            articles_df: DataFrame with 'pmid', 'title', 'abstract'
        """
        logger.info(f"Building semantic index for {len(articles_df)} articles")
        
        # Generate embeddings for title + abstract
        texts = (
            articles_df['title'] + " " + articles_df['abstract']
        ).tolist()
        
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32
        )
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product = cosine
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
        
        # Store PMID mapping
        self.pmid_mapping = {i: pmid for i, pmid in enumerate(articles_df['pmid'])}
        
        logger.info(f"Index built with {self.index.ntotal} vectors")
        
    def search(
        self, 
        query: str, 
        top_k: int = 20
    ) -> List[Tuple[str, float]]:
        """
        Semantic search for query.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of (pmid, similarity_score) tuples
        """
        # Encode query
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        similarities, indices = self.index.search(query_embedding, top_k)
        
        # Map back to PMIDs
        results = [
            (self.pmid_mapping[idx], float(sim))
            for idx, sim in zip(indices[0], similarities[0])
        ]
        
        return results
        
    def find_similar_papers(
        self, 
        pmid: str, 
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """Find papers similar to given PMID."""
        # Get embedding for this PMID
        idx = [k for k, v in self.pmid_mapping.items() if v == pmid][0]
        embedding = self.index.reconstruct(idx).reshape(1, -1)
        
        # Search
        similarities, indices = self.index.search(embedding, top_k + 1)
        
        # Skip first result (itself)
        results = [
            (self.pmid_mapping[idx], float(sim))
            for idx, sim in zip(indices[0][1:], similarities[0][1:])
        ]
        
        return results
        
    def save_index(self, filepath: str) -> None:
        """Save FAISS index and mappings."""
        faiss.write_index(self.index, f"{filepath}.index")
        with open(f"{filepath}.pkl", "wb") as f:
            pickle.dump(self.pmid_mapping, f)
            
    def load_index(self, filepath: str) -> None:
        """Load FAISS index and mappings."""
        self.index = faiss.read_index(f"{filepath}.index")
        with open(f"{filepath}.pkl", "rb") as f:
            self.pmid_mapping = pickle.load(f)
```

#### 2.2 Integration Points

**Enhance search.py**:
```python
def search_semantic(query: str, top_k: int = 20) -> List[str]:
    """Semantic search using embeddings."""
    engine = SemanticSearchEngine()
    engine.load_index("data/embeddings/pubmed_index")
    results = engine.search(query, top_k)
    return [pmid for pmid, score in results]
```

**Dashboard Features**:
- "Semantic Search" toggle vs keyword search
- "Find Similar Papers" button on each result
- Similarity scores displayed
- "Recommended for you" based on reading history

#### 2.3 Performance Optimizations

```python
# Redis caching for embeddings
import redis

class CachedSemanticSearch(SemanticSearchEngine):
    """Semantic search with Redis caching."""
    
    def __init__(self, redis_client: redis.Redis, **kwargs):
        super().__init__(**kwargs)
        self.cache = redis_client
        
    def _get_cached_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding from cache."""
        key = f"emb:{hash(text)}"
        cached = self.cache.get(key)
        if cached:
            return pickle.loads(cached)
        return None
        
    def _cache_embedding(self, text: str, embedding: np.ndarray):
        """Cache embedding."""
        key = f"emb:{hash(text)}"
        self.cache.setex(key, 86400, pickle.dumps(embedding))  # 24h TTL
```

### Success Criteria
- [ ] Generate embeddings for 1000 papers in < 30 seconds
- [ ] Search 10k papers in < 100ms
- [ ] Semantic results better than keyword (user testing)
- [ ] "Similar papers" feature works accurately
- [ ] Cache hit rate > 80%

---

## PHASE 3: TOPIC MODELING

### Overview
Implement unsupervised topic discovery using BERTopic for modern, interpretable topic modeling.

### Technical Stack
- **Framework**: BERTopic
- **Embeddings**: Same as Phase 2 (sentence-transformers)
- **Clustering**: HDBSCAN
- **Dimensionality Reduction**: UMAP
- **Representation**: c-TF-IDF

### Implementation Plan

#### 3.1 Topic Modeling Module

**File**: `app/intelligence/topic_modeling.py`

```python
"""Topic modeling using BERTopic for research discovery."""

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
import pandas as pd
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class ResearchTopicModeler:
    """Discover research topics using BERTopic."""
    
    def __init__(self):
        """Initialize topic modeler."""
        self.model = None
        self.topics = None
        self.probs = None
        
    def fit_topics(
        self,
        articles_df: pd.DataFrame,
        n_topics: int = None,  # Auto if None
        min_topic_size: int = 10
    ) -> Tuple[List[int], List[float]]:
        """
        Discover topics from articles.
        
        Args:
            articles_df: DataFrame with abstracts
            n_topics: Number of topics (None for auto)
            min_topic_size: Minimum papers per topic
            
        Returns:
            Tuple of (topics, probabilities)
        """
        logger.info(f"Fitting topics on {len(articles_df)} articles")
        
        # Prepare documents
        docs = (
            articles_df['title'] + ". " + articles_df['abstract']
        ).tolist()
        
        # Initialize BERTopic
        sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        self.model = BERTopic(
            embedding_model=sentence_model,
            min_topic_size=min_topic_size,
            nr_topics=n_topics,
            calculate_probabilities=True,
            verbose=True
        )
        
        # Fit model
        self.topics, self.probs = self.model.fit_transform(docs)
        
        logger.info(f"Discovered {len(set(self.topics))} topics")
        
        return self.topics, self.probs
        
    def get_topic_info(self) -> pd.DataFrame:
        """Get information about all topics."""
        return self.model.get_topic_info()
        
    def get_topic_terms(self, topic_id: int, top_n: int = 10) -> List[Tuple[str, float]]:
        """Get top terms for a topic."""
        return self.model.get_topic(topic_id)[:top_n]
        
    def get_papers_in_topic(
        self,
        topic_id: int,
        articles_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Get all papers assigned to a topic."""
        mask = [t == topic_id for t in self.topics]
        return articles_df[mask]
        
    def visualize_topics(self):
        """Generate topic visualization."""
        return self.model.visualize_topics()
        
    def visualize_hierarchy(self):
        """Generate hierarchical topic view."""
        return self.model.visualize_hierarchy()
        
    def track_topic_evolution(
        self,
        articles_df: pd.DataFrame,
        timestamps: List[str]
    ):
        """Track how topics evolve over time."""
        topics_over_time = self.model.topics_over_time(
            docs=articles_df['abstract'].tolist(),
            timestamps=timestamps,
            nr_bins=20
        )
        return topics_over_time
```

#### 3.2 Dashboard Integration

```python
# In dashboard/streamlit_app.py - Topics tab

def display_topics():
    st.header("Research Topics")
    
    if st.button("Discover Topics"):
        with st.spinner("Analyzing topics..."):
            modeler = ResearchTopicModeler()
            topics, probs = modeler.fit_topics(st.session_state.articles_df)
            
            # Display topic info
            topic_info = modeler.get_topic_info()
            st.dataframe(topic_info)
            
            # Visualizations
            st.plotly_chart(modeler.visualize_topics())
            
            # Topic selection
            selected_topic = st.selectbox(
                "Explore Topic",
                options=topic_info['Topic'].tolist()
            )
            
            # Papers in topic
            papers = modeler.get_papers_in_topic(
                selected_topic,
                st.session_state.articles_df
            )
            st.write(f"Found {len(papers)} papers in this topic")
            st.dataframe(papers[['title', 'authors', 'year']])
```

### Success Criteria
- [ ] Discover coherent topics automatically
- [ ] Topic labels interpretable by domain experts
- [ ] Visualizations interactive and informative
- [ ] Topic evolution tracking works
- [ ] Processing time < 2 min for 1000 papers

---

## PHASES 4-7: BRIEF SPECIFICATIONS

### Phase 4: Trend Detection

**Key Components**:
- Publication velocity analysis
- Exponential growth detection
- Burst detection (Kleinberg algorithm)
- Statistical significance testing

**Core Function**:
```python
def detect_publication_bursts(articles_df: pd.DataFrame) -> List[Dict]:
    """Detect publication bursts using Kleinberg algorithm."""
    # Group by year
    yearly_counts = articles_df.groupby('year').size()
    
    # Calculate growth rates
    growth_rates = yearly_counts.pct_change()
    
    # Identify bursts (growth > 2 std dev)
    threshold = growth_rates.mean() + 2 * growth_rates.std()
    bursts = growth_rates[growth_rates > threshold]
    
    return bursts.to_dict()
```

### Phase 5: Author Collaboration Networks

**Key Components**:
- Co-authorship graph
- Community detection (Louvain)
- Collaboration frequency
- Key researcher identification

**Core Function**:
```python
def build_author_network(articles_df: pd.DataFrame) -> nx.Graph:
    """Build undirected co-authorship graph."""
    G = nx.Graph()
    
    for _, row in articles_df.iterrows():
        authors = row['authors']
        # Add edges between all co-authors
        for i, author1 in enumerate(authors):
            for author2 in authors[i+1:]:
                if G.has_edge(author1, author2):
                    G[author1][author2]['weight'] += 1
                else:
                    G.add_edge(author1, author2, weight=1)
    
    return G
```

### Phase 6: AI Research Assistant

**Key Components**:
- OpenAI GPT-4 integration
- Google Gemini integration
- Local model fallback
- Prompt engineering for scientific text

**Core Function**:
```python
def summarize_with_llm(
    abstract: str,
    provider: str = "openai"
) -> Dict[str, str]:
    """Generate AI summary of abstract."""
    prompt = f"""Summarize this scientific abstract in 2-3 sentences.
    Focus on: research question, methodology, key findings.
    
    Abstract: {abstract}
    
    Summary:"""
    
    if provider == "openai":
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return {"summary": response.choices[0].message.content}
    # Add Gemini, local model support
```

### Phase 7: Production Infrastructure

**Key Components**:
1. **PostgreSQL Database**
   - SQLAlchemy models
   - Alembic migrations
   - Connection pooling

2. **Redis Caching**
   - Embedding cache
   - Search result cache
   - Session management

3. **Docker Setup**
   ```dockerfile
   # Dockerfile
   FROM python:3.12-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["streamlit", "run", "dashboard/streamlit_app.py"]
   ```

4. **CI/CD Pipeline**
   ```yaml
   # .github/workflows/tests.yml
   name: Tests
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Run tests
           run: pytest --cov=app tests/
   ```

---

## UPDATED README OUTLINE

```markdown
# PubMed Research Intelligence Platform

> Advanced research discovery tool with citation analysis, semantic search, and AI-powered insights

[![Tests](badge)]() [![Coverage](badge)]() [![License](badge)]()

## Features

### 🔍 Intelligent Search
- **Semantic Search**: Find papers by meaning, not just keywords
- **Citation Network**: Discover influential papers and research communities
- **Similar Papers**: AI-powered recommendations

### 📊 Research Analytics
- **Topic Modeling**: Automatic research theme discovery
- **Trend Detection**: Identify emerging research areas
- **Author Networks**: Map collaboration patterns

### 🤖 AI Research Assistant
- **Smart Summaries**: GPT-4 powered paper summaries
- **Gap Analysis**: Identify research opportunities
- **Literature Reviews**: Auto-generate review sections

## Quick Start

```bash
# Install
git clone https://github.com/username/pubmed-research-analyzer
cd pubmed-research-analyzer
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your NCBI API key

# Run
streamlit run dashboard/streamlit_app.py
```

## Architecture

[Architecture diagram]

## Documentation

- [User Guide](docs/user_guide.md)
- [API Reference](docs/api_reference.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)

## Examples

### Citation Network Analysis
```python
from app.intelligence.citation_network import CitationNetworkBuilder

builder = CitationNetworkBuilder()
graph = builder.build_network(pmids)
influential = analyzer.identify_influential_papers()
```

### Semantic Search
```python
from app.intelligence.semantic_search import SemanticSearchEngine

engine = SemanticSearchEngine()
results = engine.search("CRISPR gene editing", top_k=20)
```

## Tech Stack

- **Backend**: Python 3.12+
- **NLP**: sentence-transformers, BERTopic
- **Graph**: NetworkX
- **AI**: OpenAI, Google Gemini
- **Database**: PostgreSQL, Redis
- **Frontend**: Streamlit
- **Deployment**: Docker, GitHub Actions

## License

MIT License

## Citation

If you use this tool in your research, please cite:
[Citation format]
```

---

## FINAL IMPLEMENTATION TIMELINE

### Week 1-3: Foundation (Phase 1)
- Citation network core implementation
- Dashboard integration
- Basic testing

### Week 4-6: Intelligence (Phases 2-3)
- Semantic search implementation
- Topic modeling integration
- Advanced visualizations

### Week 7-9: Analytics & AI (Phases 4-6)
- Trend detection
- Author networks
- AI assistant integration

### Week 10-12: Production (Phase 7)
- Database migration
- Docker setup
- CI/CD pipeline
- Comprehensive testing
- Documentation

---

## SUCCESS METRICS TRACKING

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Portfolio Score | 7.0 | 9.0 | 🎯 |
| Test Coverage | 15% | 70%+ | 📈 |
| Features | 7 | 13 | 📊 |
| Documentation | Good | Excellent | ✍️ |
| Deployment | None | Docker+CI/CD | 🚀 |

---

## CONCLUSION

This implementation guide provides a complete roadmap to transform the PubMed Research Analyzer into a top-tier research intelligence platform. By systematically implementing these phases, the project will move from a 7/10 "Strong Portfolio Project" to a 9/10 "Outstanding Portfolio Project" suitable for competitive bioinformatics and AI analyst positions.

**Next Actions**:
1. Review and approve this guide
2. Set up development environment
3. Begin Phase 1 implementation
4. Track progress against milestones
5. Iterate and improve

**Questions? Ready to start implementation?**