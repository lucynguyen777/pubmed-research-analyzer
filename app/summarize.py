"""
AI-powered abstract summarization with fallback to extractive summarization.
"""

from typing import Dict, Any, List, Optional
import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)


def summarize_abstract(
    abstract: str,
    api_key: Optional[str] = None,
    provider: str = "extractive"
) -> Dict[str, Any]:
    """
    Summarize an abstract using AI or extractive methods.

    Args:
        abstract: Abstract text to summarize
        api_key: API key for AI provider (OpenAI or Gemini)
        provider: Provider to use ("openai", "gemini", or "extractive")

    Returns:
        Dictionary with summary, key_findings, and limitations
    """
    if not abstract or abstract == "N/A":
        logger.warning("Empty or invalid abstract provided")
        return {
            "summary": "No abstract available",
            "key_findings": [],
            "limitations": []
        }

    # If no API key, fall back to extractive summarization
    if not api_key or provider == "extractive":
        return _extractive_summarization(abstract)

    # Placeholder for future AI integration
    if provider == "openai":
        return _openai_summarization(abstract, api_key)
    elif provider == "gemini":
        return _gemini_summarization(abstract, api_key)

    # Default to extractive
    return _extractive_summarization(abstract)


def _extractive_summarization(abstract: str) -> Dict[str, Any]:
    """
    Simple extractive summarization fallback.

    Args:
        abstract: Abstract text

    Returns:
        Dictionary with summary components
    """
    sentences = _split_sentences(abstract)

    if not sentences:
        return {
            "summary": "Unable to parse abstract",
            "key_findings": [],
            "limitations": []
        }

    # Extract first 2-3 sentences as summary
    summary = " ".join(sentences[:min(3, len(sentences))])

    # Extract key findings (sentences with results/findings keywords)
    key_findings = _extract_key_findings(sentences)

    # Extract limitations
    limitations = _extract_limitations(sentences)

    logger.info("Extractive summarization completed")
    return {
        "summary": summary,
        "key_findings": key_findings,
        "limitations": limitations
    }


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Simple sentence splitting
    text = text.replace("\n", " ").strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def _extract_key_findings(sentences: List[str]) -> List[str]:
    """Extract sentences likely to contain key findings."""
    finding_keywords = [
        "found", "showed", "demonstrated", "revealed", "observed",
        "results", "concluded", "significant", "increased", "decreased"
    ]

    findings = []
    for sentence in sentences:
        lower_sent = sentence.lower()
        if any(keyword in lower_sent for keyword in finding_keywords):
            findings.append(sentence)

    return findings[:3]  # Top 3 findings


def _extract_limitations(sentences: List[str]) -> List[str]:
    """Extract sentences discussing limitations."""
    limitation_keywords = [
        "limitation", "limited", "however", "although", "despite",
        "lack of", "small sample", "further research", "future studies"
    ]

    limitations = []
    for sentence in sentences:
        lower_sent = sentence.lower()
        if any(keyword in lower_sent for keyword in limitation_keywords):
            limitations.append(sentence)

    return limitations[:2]  # Top 2 limitations


def _openai_summarization(abstract: str, api_key: str) -> Dict[str, Any]:
    """
    Placeholder for OpenAI API integration.

    Args:
        abstract: Abstract text
        api_key: OpenAI API key

    Returns:
        Summary dictionary
    """
    logger.info("OpenAI summarization not implemented - using extractive fallback")
    # TODO: Implement OpenAI API call
    # Example:
    # import openai
    # openai.api_key = api_key
    # response = openai.ChatCompletion.create(...)
    return _extractive_summarization(abstract)


def _gemini_summarization(abstract: str, api_key: str) -> Dict[str, Any]:
    """
    Placeholder for Gemini API integration.

    Args:
        abstract: Abstract text
        api_key: Gemini API key

    Returns:
        Summary dictionary
    """
    logger.info("Gemini summarization not implemented - using extractive fallback")
    # TODO: Implement Gemini API call
    return _extractive_summarization(abstract)


def batch_summarize(abstracts: List[str]) -> List[Dict[str, Any]]:
    """
    Summarize multiple abstracts.

    Args:
        abstracts: List of abstract texts

    Returns:
        List of summary dictionaries
    """
    summaries = []
    for abstract in abstracts:
        summary = summarize_abstract(abstract)
        summaries.append(summary)

    logger.info(f"Batch summarized {len(summaries)} abstracts")
    return summaries