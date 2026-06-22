"""
PubMed search functionality using NCBI Entrez API.
"""

from typing import List, Dict, Any, Optional, cast
from Bio import Entrez
import logging

logger = logging.getLogger(__name__)


def search_pubmed(
    query: str,
    max_results: int = 20,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[str]:
    """
    Search PubMed for articles matching the query.

    Args:
        query: Search query (supports keywords, authors, journals)
        max_results: Maximum number of results to retrieve
        date_from: Start date filter (YYYY/MM/DD format)
        date_to: End date filter (YYYY/MM/DD format)

    Returns:
        List of PMIDs (PubMed IDs)

    Raises:
        Exception: If API call fails
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")

    if max_results < 1 or max_results > 10000:
        raise ValueError("max_results must be between 1 and 10000")

    # Build date range filter
    date_filter = ""
    if date_from and date_to:
        date_filter = f' AND ("{date_from}"[PDAT] : "{date_to}"[PDAT])'

    full_query = query + date_filter

    try:
        logger.info(f"Searching PubMed with query: {full_query}")
        handle = Entrez.esearch(db="pubmed", term=full_query, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()

        record_dict = cast(Dict[str, Any], record)
        pmids = record_dict.get("IdList", [])
        logger.info(f"Found {len(pmids)} articles")
        return pmids

    except Exception as exc:
        logger.error(f"PubMed search failed: {exc}")
        raise


def search_by_keyword(query: str, max_results: int = 20) -> List[str]:
    """
    Search by keywords in title and abstract.

    Args:
        query: Keyword search terms
        max_results: Maximum results to return

    Returns:
        List of PMIDs
    """
    return search_pubmed(query, max_results)


def search_by_author(author: str, max_results: int = 20) -> List[str]:
    """
    Search for articles by a specific author.

    Args:
        author: Author name (Last name, First name)
        max_results: Maximum results to return

    Returns:
        List of PMIDs
    """
    query = f'"{author}"[AUTHOR]'
    return search_pubmed(query, max_results)


def search_by_journal(journal: str, max_results: int = 20) -> List[str]:
    """
    Search for articles from a specific journal.

    Args:
        journal: Journal name
        max_results: Maximum results to return

    Returns:
        List of PMIDs
    """
    query = f'"{journal}"[TA]'
    return search_pubmed(query, max_results)


def search_with_filters(
    query: str,
    max_results: int = 20,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    article_type: Optional[str] = None,
) -> List[str]:
    """
    Search with advanced filters.

    Args:
        query: Base search query
        max_results: Maximum results
        date_from: Start date (YYYY/MM/DD)
        date_to: End date (YYYY/MM/DD)
        article_type: Filter by article type (e.g., "Review", "Research")

    Returns:
        List of PMIDs
    """
    filters = query

    if article_type:
        filters += f' AND "{article_type}"[PT]'

    return search_pubmed(filters, max_results, date_from, date_to)