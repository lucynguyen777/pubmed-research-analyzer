"""
Utility functions for the PubMed Research Analyzer.
"""

import time
import logging
from typing import Dict, Any, List, Optional
import requests
import re

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Simple exponential backoff retry decorator
def retry(
    max_attempts: int = 3,
    backoff_factor: float = 1.5,
    allowed_exceptions: tuple = (requests.exceptions.RequestException,),
):
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = 1.0
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except allowed_exceptions as exc:
                    attempt += 1
                    if attempt == max_attempts:
                        logger.error(f"Max retries reached for {func.__name__}: {exc}")
                        raise
                    logger.warning(
                        f"Retry {attempt}/{max_attempts} for {func.__name__} after {delay}s – {exc}"
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator

@retry()
def safe_get(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> requests.Response:
    """
    Perform a GET request with retry logic.
    """
    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    return response

def clean_text(text: str) -> str:
    """
    Remove non‑alphanumeric characters and collapse whitespace.
    """
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    return text.strip().lower()

def extract_keywords(text: str, stopwords: set, min_len: int = 3) -> List[str]:
    """
    Tokenize text, remove stopwords and short tokens, return list of keywords.
    """
    tokens = clean_text(text).split()
    keywords = [t for t in tokens if t not in stopwords and len(t) >= min_len]
    return keywords

def load_stopwords() -> set:
    """
    Load a basic English stopword list.
    """
    # Minimal built‑in list; can be extended later.
    default_stopwords = {
        "the", "and", "for", "with", "that", "from", "this", "these",
        "those", "are", "was", "were", "has", "have", "had", "but",
        "not", "can", "could", "should", "would", "may", "might",
        "its", "it", "of", "in", "on", "at", "by", "to", "a", "an",
        "or", "as", "if", "we", "our", "you", "your", "they", "their"
    }
    return default_stopwords