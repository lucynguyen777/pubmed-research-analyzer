# PubMed Research Analyzer

A production-quality scientific literature analysis platform that enables researchers to search PubMed articles, analyze metadata, summarize abstracts with AI, compare multiple papers, and export results.

## Overview

PubMed Research Analyzer is a Python-based application that leverages the NCBI Entrez API to fetch and analyze scientific publications. It provides an intuitive Streamlit dashboard for exploring publication trends, identifying research gaps, comparing multiple articles, and generating reports.

### Purpose

- Search PubMed for scientific articles by keyword, author, or journal
- Extract and analyze metadata (authors, journals, dates, abstracts)
- Generate analytics (publications per year, top journals, top authors, keyword frequency)
- Summarize abstracts with AI (OpenAI/Gemini) or extractive fallback
- Identify research gaps and future directions
- Compare multiple articles across methodology, findings, and limitations
- Export results to CSV or Excel formats

## Features

| Feature | Description |
|---------|-------------|
| **Advanced Search** | Keyword, author, journal search with date filtering |
| **Article Fetching** | Fetch PMIDs, titles, authors, journals, abstracts, DOIs |
| **Research Analytics** | Publications timeline, top journals, top authors, keywords |
| **AI Summarization** | Extractive fallback or OpenAI/Gemini API integration |
| **Research Gap Detection** | Identify recurring limitations, underexplored topics, future directions |
| **Literature Comparison** | Compare methodology, sample size, findings, limitations |
| **Export Functionality** | CSV, Excel with multiple sheets for analytics |
| **Interactive Dashboard** | Streamlit UI with Plotly visualizations |

## Installation

### Prerequisites

- Python 3.12 or higher
- pip package manager
- NCBI account (for Entrez API access)

### Setup

```bash
# Clone the repository
cd pubmed-research-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env file with your API keys
```

### Environment Configuration

Create a `.env` file in the project root:

```env
# NCBI Entrez API settings
NCBI_EMAIL=your_email@example.com
NCBI_API_KEY=your_ncbi_api_key_here

# OpenAI API (optional for enhanced summarization)
OPENAI_API_KEY=your_openai_api_key_here

# Gemini API (optional for enhanced summarization)
GEMINI_API_KEY=your_gemini_api_key_here

# App settings
MAX_RESULTS_DEFAULT=20
EXPORT_DIR=exports
```

To get an NCBI API key:
1. Visit https://www.ncbi.nlm.nih.gov/account/
2. Sign in and request an API key
3. The key is free and typically granted immediately

## Usage

### Running the Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

The dashboard will open in your browser at `http://localhost:8501`.

### Command Line Usage

```python
from app.search import search_pubmed
from app.fetch import fetch_articles_batch
from app.analyze import analyze_publications
from app.export import export_csv

# Search for articles
pmids = search_pubmed("COVID-19 vaccine", max_results=20)

# Fetch details
df = fetch_articles_batch(pmids)

# Analyze
analytics = analyze_publications(df)

# Export
export_csv(df, "articles.csv")
```

### Using the Research Gap Detector

```python
from app.research_gap import detect_research_gaps, generate_gap_report

gaps = detect_research_gaps(df)
report = generate_gap_report(df)
print(report)
```

### Using the Literature Comparison Module

```python
from app.literature_comparison import compare_articles, generate_comparison_report

comparison = compare_articles(df, pmids=["12345678", "87654321"])
report = generate_comparison_report(df, pmids=["12345678", "87654321"])
print(report)
```

## Project Structure

```
pubmed-research-analyzer/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration and directory setup
│   ├── utils.py           # Utility functions (text processing, retry logic)
│   ├── search.py          # PubMed search functionality
│   ├── fetch.py           # Article fetching and details extraction
│   ├── analyze.py         # Analytics and metadata analysis
│   ├── export.py          # CSV/Excel export functions
│   ├── summarize.py       # AI abstract summarization
│   ├── research_gap.py    # Research gap detection
│   └── literature_comparison.py  # Article comparison module
├── dashboard/
│   └── streamlit_app.py   # Main Streamlit dashboard
├── tests/
│   ├── __init__.py
│   └── test_analyzer.py   # Unit tests
├── data/                  # Data directory (for cached data)
├── exports/               # Exported files (CSV, Excel)
├── notebooks/             # Jupyter notebooks
├── README.md
├── requirements.txt
└── .env.example
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    PubMed Research Analyzer                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Search     │───▶│   Fetch      │───▶│  Analyze     │      │
│  │   Module     │    │   Module     │    │  Module      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                    │                    │             │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   NCBI       │    │  PubMed      │    │  Analytics   │      │
│  │   Entrez API │    │  Articles    │    │  Reports     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Research    │    │ Literature   │    │   Export     │      │
│  │    Gap       │    │ Comparison   │    │   Module     │      │
│  │  Detector    │    │   Module     │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   AI         │    │ DataFrame    │    │   CSV/Excel  │      │
│  │ Summarization│    │   Views      │    │   Export     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                    ▲                    ▲
                    │                    │
              ┌─────┴──────┐    ┌───────┴──────┐
              │  Streamlit │    │  Streamlit   │
              │  Dashboard │    │   Viewer     │
              └────────────┘    └──────────────┘
```

## Error Handling

The application implements comprehensive error handling:

- **API Rate Limiting**: Automatic retry with exponential backoff
- **Invalid Queries**: Validation of search parameters
- **Missing Data**: Graceful handling of missing fields
- **Network Failures**: Connection timeout and retry logic
- **Meaningful Messages**: User-friendly error messages

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

To run specific test classes:

```bash
pytest tests/test_analyzer.py::TestSearch -v
pytest tests/test_analyzer.py::TestAnalyze -v
pytest tests/test_analyzer.py::TestExport -v
```

## Future Improvements

- [ ] **AI-Powered Literature Review**: Generate comprehensive review summaries
- [ ] **Research Gap Detection**: Automatic identification of underexplored areas
- [ ] **Multi-Paper Comparison**: Compare methodology and findings across studies
- [ ] **Citation Network Analysis**: Visualize citation relationships
- [ ] **Trend Analysis**: Identify emerging research trends
- [ ] **Author Network Analysis**: Map collaboration networks
- [ ] **Journal Impact Analysis**: Assess journal influence metrics
- [ ] **Abstract Clustering**: Group similar papers using NLP embeddings
- [ ] **Sentiment Analysis**: Analyze sentiment in abstracts
- [ ] **Export to BibTeX**: For reference management integration

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues and feature requests, please file an issue on GitHub.

## Acknowledgments

- Powered by NCBI PubMed and Entrez API
- Built with Streamlit, Pandas, Plotly, and Biopython