"""
Research analytics module for analyzing publication metadata.
"""

from typing import Dict, Any, List
import pandas as pd
from collections import Counter
import logging
from app.utils import extract_keywords, load_stopwords

logger = logging.getLogger(__name__)


def analyze_publications(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive analytics from article metadata.

    Args:
        df: DataFrame with article data

    Returns:
        Dictionary with analytics results
    """
    if df.empty:
        logger.warning("Empty DataFrame provided for analysis")
        return {
            "year_counts": {},
            "journal_counts": {},
            "author_counts": {},
            "keyword_counts": {},
        }

    analytics = {
        "year_counts": get_publications_per_year(df),
        "journal_counts": get_top_journals(df),
        "author_counts": get_top_authors(df),
        "keyword_counts": get_keyword_frequency(df),
    }

    logger.info("Analysis completed successfully")
    return analytics


def get_publications_per_year(df: pd.DataFrame) -> Dict[str, int]:
    """
    Count publications per year.

    Args:
        df: Article DataFrame

    Returns:
        Dictionary with year as key and count as value
    """
    if df.empty or "pub_date" not in df.columns:
        return {}

    # Extract year from pub_date
    years = []
    for date in df["pub_date"]:
        if date and date != "N/A":
            try:
                year = str(date).split("-")[0]
                years.append(int(year))
            except (ValueError, IndexError):
                pass

    year_counts = dict(sorted(Counter(years).items()))
    logger.info(f"Publications per year: {len(year_counts)} distinct years")
    return year_counts


def get_top_journals(df: pd.DataFrame, top_n: int = 10) -> Dict[str, int]:
    """
    Get top journals by publication count.

    Args:
        df: Article DataFrame
        top_n: Number of top journals to return

    Returns:
        Dictionary with journal names and counts
    """
    if df.empty or "journal" not in df.columns:
        return {}

    journals = [j for j in df["journal"] if j and j != "N/A"]
    journal_counts = Counter(journals).most_common(top_n)
    result = {journal: count for journal, count in journal_counts}

    logger.info(f"Top {top_n} journals identified")
    return result


def get_top_authors(df: pd.DataFrame, top_n: int = 10) -> Dict[str, int]:
    """
    Get top authors by publication count.

    Args:
        df: Article DataFrame
        top_n: Number of top authors to return

    Returns:
        Dictionary with author names and counts
    """
    if df.empty or "authors" not in df.columns:
        return {}

    all_authors = []
    for authors_list in df["authors"]:
        if isinstance(authors_list, list):
            all_authors.extend(authors_list)

    author_counts = Counter(all_authors).most_common(top_n)
    result = {author: count for author, count in author_counts}

    logger.info(f"Top {top_n} authors identified")
    return result


def get_keyword_frequency(df: pd.DataFrame, top_n: int = 20) -> Dict[str, int]:
    """
    Extract keywords from titles and abstracts.

    Args:
        df: Article DataFrame
        top_n: Number of top keywords to return

    Returns:
        Dictionary with keywords and frequencies
    """
    if df.empty:
        return {}

    stopwords = load_stopwords()
    all_keywords = []

    # Extract from titles
    if "title" in df.columns:
        for title in df["title"]:
            if title and title != "N/A":
                keywords = extract_keywords(str(title), stopwords)
                all_keywords.extend(keywords)

    # Extract from abstracts
    if "abstract" in df.columns:
        for abstract in df["abstract"]:
            if abstract and abstract != "N/A":
                keywords = extract_keywords(str(abstract), stopwords)
                all_keywords.extend(keywords)

    keyword_counts = Counter(all_keywords).most_common(top_n)
    result = {keyword: count for keyword, count in keyword_counts}

    logger.info(f"Top {top_n} keywords extracted")
    return result


def get_author_publication_timeline(df: pd.DataFrame, author: str) -> Dict[str, int]:
    """
    Get publication timeline for a specific author.

    Args:
        df: Article DataFrame
        author: Author name to filter

    Returns:
        Dictionary with years and publication counts
    """
    if df.empty or "authors" not in df.columns or "pub_date" not in df.columns:
        return {}

    # Filter articles by author
    author_articles = []
    for idx, authors_list in enumerate(df["authors"]):
        if isinstance(authors_list, list) and author in authors_list:
            author_articles.append(df.iloc[idx])

    if not author_articles:
        logger.warning(f"No articles found for author: {author}")
        return {}

    author_df = pd.DataFrame(author_articles)
    return get_publications_per_year(author_df)


def get_journal_trend(df: pd.DataFrame, journal: str) -> Dict[str, int]:
    """
    Get publication trend for a specific journal.

    Args:
        df: Article DataFrame
        journal: Journal name to filter

    Returns:
        Dictionary with years and publication counts
    """
    if df.empty or "journal" not in df.columns:
        return {}

    journal_df = df[df["journal"] == journal]
    if journal_df.empty:
        logger.warning(f"No articles found for journal: {journal}")
        return {}

    return get_publications_per_year(journal_df)