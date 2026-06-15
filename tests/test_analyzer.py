"""
Unit tests for PubMed Research Analyzer.
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.search import search_pubmed
from app.fetch import fetch_article_details, fetch_articles_batch
from app.analyze import analyze_publications, get_publications_per_year, get_top_journals, get_top_authors
from app.export import export_csv, export_excel
from app.utils import clean_text, extract_keywords, load_stopwords
from app.summarize import summarize_abstract


class TestUtils:
    """Test utility functions."""
    
    def test_clean_text(self):
        """Test text cleaning."""
        assert clean_text("Hello, World!   ") == "hello world"
        assert clean_text("A-B-C 123") == "abc 123"
        assert clean_text("") == ""
    
    def test_load_stopwords(self):
        """Test stopwords loading."""
        stopwords = load_stopwords()
        assert isinstance(stopwords, set)
        assert "the" in stopwords
        assert "and" in stopwords
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        stopwords = load_stopwords()
        text = "The quick brown fox jumps over the lazy dog"
        keywords = extract_keywords(text, stopwords)
        assert "quick" in keywords
        assert "brown" in keywords
        assert "the" not in keywords  # stopword removed


class TestSearch:
    """Test search functionality."""
    
    def test_search_pubmed_invalid_input(self):
        """Test invalid search input."""
        with pytest.raises(ValueError):
            search_pubmed("", max_results=10)
        
        with pytest.raises(ValueError):
            search_pubmed("test", max_results=0)
    
    def test_search_pubmed_mock(self, monkeypatch):
        """Test search with mock response."""
        from unittest.mock import MagicMock

        mock_handle = MagicMock()
        monkeypatch.setattr("app.search.Entrez.esearch", lambda **kwargs: mock_handle)
        monkeypatch.setattr("app.search.Entrez.read", lambda handle: {"IdList": ["12345678", "87654321"]})

        pmids = search_pubmed("test query", max_results=2)
        assert len(pmids) == 2
        assert "12345678" in pmids


class TestFetch:
    """Test article fetching."""
    
    def test_fetch_article_details_empty(self):
        """Test fetching empty PMID."""
        with pytest.raises(ValueError):
            fetch_article_details("")
    
    def test_empty_article_record(self):
        """Test empty article record creation."""
        from app.fetch import _empty_article_record
        record = _empty_article_record("12345678")
        assert record["pmid"] == "12345678"
        assert record["title"] == "N/A"
        assert record["journal"] == "N/A"
        assert record["abstract"] == "N/A"
    
    def test_fetch_articles_batch_empty(self):
        """Test batch fetch with empty list."""
        df = fetch_articles_batch([])
        assert df.empty


class TestAnalyze:
    """Test analytics functions."""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing."""
        data = {
            "pmid": ["1", "2", "3"],
            "title": ["Study A", "Study B", "Study C"],
            "journal": ["Journal X", "Journal X", "Journal Y"],
            "pub_date": ["2020-01-01", "2021-05-15", "2020-08-20"],
            "authors": [["Smith, John"], ["Doe, Jane"], ["Smith, John", "Doe, Jane"]],
            "abstract": ["Abstract for study A", "Abstract for study B", "Abstract for study C"]
        }
        return pd.DataFrame(data)
    
    def test_get_publications_per_year(self, sample_dataframe):
        """Test year count analysis."""
        year_counts = get_publications_per_year(sample_dataframe)
        assert 2020 in year_counts
        assert 2021 in year_counts
        assert year_counts[2020] == 2  # Two articles in 2020
        assert year_counts[2021] == 1  # One article in 2021
    
    def test_get_top_journals(self, sample_dataframe):
        """Test journal count analysis."""
        journal_counts = get_top_journals(sample_dataframe, top_n=2)
        assert "Journal X" in journal_counts
        assert "Journal Y" in journal_counts
        assert journal_counts["Journal X"] == 2  # Two articles in Journal X
    
    def test_get_top_authors(self, sample_dataframe):
        """Test author count analysis."""
        author_counts = get_top_authors(sample_dataframe, top_n=2)
        assert "Smith, John" in author_counts
        assert "Doe, Jane" in author_counts
        assert author_counts["Smith, John"] == 2  # Smith appears in 2 articles
    
    def test_analyze_publications(self, sample_dataframe):
        """Test comprehensive analysis."""
        analytics = analyze_publications(sample_dataframe)
        assert "year_counts" in analytics
        assert "journal_counts" in analytics
        assert "author_counts" in analytics
        assert "keyword_counts" in analytics


class TestSummarize:
    """Test summarization functions."""
    
    def test_summarize_abstract_empty(self):
        """Test summarization with empty abstract."""
        summary = summarize_abstract("")
        assert summary["summary"] == "No abstract available"
        assert len(summary["key_findings"]) == 0
    
    def test_summarize_abstract_with_text(self):
        """Test summarization with actual text."""
        abstract = "This study found that treatment A was effective. However, the sample size was small. Future research should investigate larger populations."
        summary = summarize_abstract(abstract)
        assert "summary" in summary
        assert "key_findings" in summary
        assert "limitations" in summary
        assert len(summary["key_findings"]) >= 0
        assert len(summary["limitations"]) >= 0


class TestExport:
    """Test export functions."""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["A", "B", "C"]
        })
    
    def test_export_csv(self, sample_dataframe, tmp_path, monkeypatch):
        """Test CSV export."""
        # Mock EXPORTS_DIR to use temp directory
        monkeypatch.setattr("app.export.EXPORTS_DIR", tmp_path)
        
        filepath = export_csv(sample_dataframe, "test.csv")
        assert Path(filepath).exists()
        assert Path(filepath).suffix == ".csv"
        
        # Verify content
        loaded_df = pd.read_csv(filepath)
        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == ["col1", "col2"]
    
    def test_export_csv_empty(self, sample_dataframe, tmp_path, monkeypatch):
        """Test CSV export with empty DataFrame."""
        monkeypatch.setattr("app.export.EXPORTS_DIR", tmp_path)
        
        empty_df = pd.DataFrame()
        filepath = export_csv(empty_df, "empty.csv")
        assert filepath == ""  # Should return empty string for empty DataFrame
    
    def test_export_excel(self, sample_dataframe, tmp_path, monkeypatch):
        """Test Excel export."""
        # Mock EXPORTS_DIR to use temp directory
        monkeypatch.setattr("app.export.EXPORTS_DIR", tmp_path)
        
        filepath = export_excel(sample_dataframe, "test.xlsx")
        assert Path(filepath).exists()
        assert Path(filepath).suffix == ".xlsx"
        
        # Verify content
        loaded_df = pd.read_excel(filepath)
        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == ["col1", "col2"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])