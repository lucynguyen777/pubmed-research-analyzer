"""
Article fetching and details extraction from PubMed.
"""

from typing import Dict, Any, Optional, List
import pandas as pd
from Bio import Entrez
import logging

logger = logging.getLogger(__name__)


def fetch_article_details(pmid: str) -> Dict[str, Any]:
    """
    Fetch detailed information for a single article.

    Args:
        pmid: PubMed ID

    Returns:
        Dictionary with article metadata
    """
    if not pmid or not isinstance(pmid, str):
        raise ValueError("PMID must be a non-empty string")

    try:
        logger.info(f"Fetching details for PMID: {pmid}")
        handle = Entrez.efetch(db="pubmed", id=pmid, rettype="xml")
        record = Entrez.read(handle)
        handle.close()

        if not record.get("PubmedArticle"):
            logger.warning(f"No article found for PMID: {pmid}")
            return _empty_article_record(pmid)

        article = record["PubmedArticle"][0]
        return _parse_article(article, pmid)

    except Exception as exc:
        logger.error(f"Failed to fetch PMID {pmid}: {exc}")
        return _empty_article_record(pmid)


def _empty_article_record(pmid: str) -> Dict[str, Any]:
    """Create an empty record structure."""
    return {
        "pmid": pmid,
        "title": "N/A",
        "authors": [],
        "journal": "N/A",
        "pub_date": "N/A",
        "doi": "N/A",
        "abstract": "N/A",
    }


def _parse_article(article: Dict[str, Any], pmid: str) -> Dict[str, Any]:
    """Parse article XML into structured data."""
    med_citation = article.get("MedlineCitation", {})
    article_data = med_citation.get("Article", {})

    # Title
    title = article_data.get("ArticleTitle", "N/A")
    if isinstance(title, list):
        title = "".join(title) if title else "N/A"

    # Authors
    authors = _extract_authors(article_data)

    # Journal
    journal = article_data.get("Journal", {}).get("Title", "N/A")

    # Publication Date
    pub_date = _extract_pub_date(article_data)

    # DOI
    doi = _extract_doi(article_data)

    # Abstract
    abstract = _extract_abstract(article_data)

    return {
        "pmid": pmid,
        "title": str(title),
        "authors": authors,
        "journal": str(journal),
        "pub_date": pub_date,
        "doi": doi,
        "abstract": abstract,
    }


def _extract_authors(article_data: Dict[str, Any]) -> List[str]:
    """Extract author list from article."""
    authors = []
    author_list = article_data.get("AuthorList", [])

    if isinstance(author_list, dict):
        author_list = [author_list]

    for author in author_list:
        if isinstance(author, dict):
            last_name = author.get("LastName", "")
            first_name = author.get("ForeName", "")
            if last_name:
                name = f"{last_name}, {first_name}" if first_name else last_name
                authors.append(name)

    return authors


def _extract_pub_date(article_data: Dict[str, Any]) -> str:
    """Extract publication date."""
    pub_date = article_data.get("ArticleDate", article_data.get("PubDate", {}))

    if isinstance(pub_date, list):
        pub_date = pub_date[0] if pub_date else {}

    if isinstance(pub_date, dict):
        year = pub_date.get("Year", "")
        month = pub_date.get("Month", "01")
        day = pub_date.get("Day", "01")
        if year:
            return f"{year}-{month}-{day}"

    return "N/A"


def _extract_doi(article_data: Dict[str, Any]) -> str:
    """Extract DOI from article."""
    article_id_list = article_data.get("ArticleIdList", [])

    if isinstance(article_id_list, dict):
        article_id_list = [article_id_list]

    for article_id in article_id_list:
        if isinstance(article_id, dict):
            if article_id.get("IdType") == "doi":
                return str(article_id.get("#text", "N/A"))

    return "N/A"


def _extract_abstract(article_data: Dict[str, Any]) -> str:
    """Extract abstract text."""
    abstract = article_data.get("Abstract", {})

    if isinstance(abstract, dict):
        abstract_text = abstract.get("AbstractText", [])
        if isinstance(abstract_text, list):
            abstract_text = " ".join([str(t) for t in abstract_text if t])
        else:
            abstract_text = str(abstract_text) if abstract_text else "N/A"
        return abstract_text

    return "N/A"


def fetch_articles_batch(pmids: List[str]) -> pd.DataFrame:
    """
    Fetch details for multiple articles and return as DataFrame.

    Args:
        pmids: List of PubMed IDs

    Returns:
        DataFrame with article metadata
    """
    if not pmids:
        logger.warning("Empty PMID list provided")
        return pd.DataFrame()

    articles = []
    for pmid in pmids:
        article = fetch_article_details(pmid)
        articles.append(article)

    df = pd.DataFrame(articles)
    logger.info(f"Fetched details for {len(df)} articles")
    return df