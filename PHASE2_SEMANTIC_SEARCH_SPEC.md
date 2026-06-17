# Phase 2: Semantic Search Implementation Specification

## Overview
Replaces standard PubMed keyword search with semantic embedding-based similarity search using `sentence-transformers` and `faiss`. This enables searching by concepts rather than exact words, drastically improving relevance for research queries.

## 1. Directory Structure Updates
```
app/
├── intelligence/
│   ├── semantic_search.py  # New module
├── cache/
│   ├── redis_cache.py      # New module (for FAISS/embeddings persistence)
data/
├── embeddings/             # New directory (store FAISS indexes locally)
```

## 2. Dependencies
Add to `requirements.txt`:
```
sentence-transformers>=2.3.0
faiss-cpu>=1.7.4
scikit-learn>=1.4.0
redis>=5.0.1
```

## 3. Module Specifications

### `app/intelligence/semantic_search.py`
**Class: `SemanticSearchEngine`**
- `__init__(model_name="all-MiniLM-L6-v2")`: Initializes the sentence transformer.
- `embed_texts(texts: List[str]) -> np.ndarray`: Converts abstracts to dense vectors.
- `build_index(df: pd.DataFrame)`: Creates a FAISS index from current article embeddings.
- `search(query: str, top_k: int = 10) -> pd.DataFrame`: Semantically searches the index and returns ranked results.
- `find_similar_papers(pmid: str, top_k: int = 5) -> List[Dict]`: Finds papers similar to a given article.

### `app/cache/redis_cache.py` (Optional / Future-proofing)
**Class: `EmbeddingCache`**
- Manages local persistence of embeddings so we don't re-embed known PMIDs on app restart.
- Initially, use a local disk pickle/FAISS dump in `data/embeddings/` if Redis isn't running.

## 4. Dashboard Integration
In `dashboard/streamlit_app.py`:
- Update the main search to allow a toggle between "Keyword" and "Semantic" modes.
- *Wait*, PubMed API still needs initial keyword query to fetch the *base* corpus. So the pipeline is:
  1. Fetch base corpus from PubMed (e.g. 100-500 articles via broad keyword).
  2. Embed corpus locally.
  3. Perform high-precision semantic search against this local corpus.
- Or, use the semantic engine purely for the **"Similar Papers"** recommendation feature within the Dashboard overview.

## 5. Testing Strategy
- `tests/test_intelligence/test_semantic_search.py`
- Mock the transformer model to avoid large downloads during tests.
- Verify FAISS index creation and distance metrics.

## 6. Implementation Steps
1. Install dependencies.
2. Create `SemanticSearchEngine` class.
3. Write unit tests.
4. Integrate into Streamlit UI (Add "Semantic Search / Similar Papers" section).
5. Document approach.
