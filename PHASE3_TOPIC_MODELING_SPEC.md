# Phase 3: Topic Modeling & Evolution Specification

## Overview
Adds unsupervised clustering to discover Latent Topics within the PubMed search results, allowing the dashboard to automatically categorize hundreds of papers. 
Instead of relying on heavy frameworks like BERTopic right away, we will build an elegant TF-IDF + NMF (Non-negative Matrix Factorization) / LDA pipeline that runs instantly on CPU without forcing massive PyTorch dependencies on junior researchers exploring the portfolio.

## 1. Directory Structure Updates
```
app/
├── intelligence/
│   ├── topic_modeling.py   # New module
```

## 2. Module Specifications

### `app/intelligence/topic_modeling.py`
**Class: `TopicModeler`**
- `__init__(n_topics=5)`: Initializes the modeler.
- `fit(df: pd.DataFrame)`: 
  1. Extracts titles + abstracts.
  2. Runs standard English stop-word removal.
  3. Fits a `TfidfVectorizer` and an `NMF` model (from `sklearn.decomposition`).
  4. Assigns the dominant topic to each paper.
- `get_topic_words(top_n=10) -> Dict[int, List[str]]`: Returns the top descriptive words for each discovered topic.
- `get_topic_distribution() -> pd.DataFrame`: Returns count of papers per topic for visualization.

## 3. Dashboard Integration
In `dashboard/streamlit_app.py`:
- Add a new Tab: "🧠 Topic Modeling".
- Include a button to `Extract Topics`.
- Display a Bar Chart of Topic Distribution.
- Display a Dataframe showing each topic's top keywords.
- Let the user filter the main article dataframe by selecting a Topic from a dropdown.

## 4. Testing Strategy
- `tests/test_intelligence/test_topic_modeling.py`
- Create a mock dataframe of 10 distinct papers (e.g. 5 on mRNA, 5 on Transmission).
- Ensure the NMF model identifies 2 distinct topics correctly.
- Test edge cases: passing <5 papers should gracefully reduce `n_topics`.

## 5. Implementation Steps
1. Create `TopicModeler` class using `scikit-learn` NMF.
2. Write unit tests.
3. Integrate into Streamlit UI (Add "🧠 Topic Modeling" tab).
4. Verify end-to-end functionality.
