"""
Research Gap Detector - Identifies limitations, underexplored topics, and future directions.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
from collections import Counter
import logging
import re
from app.utils import extract_keywords, load_stopwords

logger = logging.getLogger(__name__)


def detect_research_gaps(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze multiple abstracts to identify research gaps.

    Args:
        df: DataFrame with article data including abstracts

    Returns:
        Dictionary with recurring_limitations, underexplored_topics, future_directions
    """
    if df.empty or "abstract" not in df.columns:
        logger.warning("Empty DataFrame or missing abstracts")
        return {
            "recurring_limitations": [],
            "underexplored_topics": [],
            "future_directions": [],
            "summary": "Insufficient data for gap analysis"
        }

    abstracts = [
        str(abstract) for abstract in df["abstract"]
        if abstract and abstract != "N/A"
    ]

    if not abstracts:
        return {
            "recurring_limitations": [],
            "underexplored_topics": [],
            "future_directions": [],
            "summary": "No valid abstracts found"
        }

    # Analyze limitations
    limitations = _extract_recurring_limitations(abstracts)

    # Identify underexplored topics
    topics = _identify_underexplored_topics(abstracts)

    # Extract future research directions
    directions = _extract_future_directions(abstracts)

    # Generate summary
    summary = _generate_gap_summary(limitations, topics, directions)

    logger.info("Research gap analysis completed")
    return {
        "recurring_limitations": limitations,
        "underexplored_topics": topics,
        "future_directions": directions,
        "summary": summary
    }


def _extract_recurring_limitations(abstracts: List[str]) -> List[Tuple[str, int]]:
    """Extract and count recurring limitations across abstracts."""
    limitation_patterns = [
        r"limitation[s]?\s+(?:of\s+)?(?:this\s+)?(?:study|research|work)?[:\s]+([^.]+)",
        r"limited\s+by\s+([^.]+)",
        r"despite\s+([^,]+),",
        r"however[,\s]+([^.]+)",
        r"small\s+sample\s+size",
        r"lack\s+of\s+([^.]+)",
        r"further\s+research\s+(?:is\s+)?needed\s+(?:to|for)\s+([^.]+)"
    ]

    all_limitations = []

    for abstract in abstracts:
        lower_abstract = abstract.lower()
        for pattern in limitation_patterns:
            matches = re.findall(pattern, lower_abstract)
            if matches:
                if isinstance(matches[0], str):
                    all_limitations.extend(matches)
                else:
                    all_limitations.append(pattern.replace(r"\s+", " ").replace("\\", ""))

    # Count frequency
    limitation_counter = Counter(all_limitations)
    # Filter out very short matches
    filtered = [(lim, count) for lim, count in limitation_counter.most_common(10)
                if len(lim) > 10]

    return filtered[:5]  # Top 5 recurring limitations


def _identify_underexplored_topics(abstracts: List[str]) -> List[Tuple[str, int]]:
    """Identify topics that are mentioned but not deeply explored."""
    underexplored_keywords = [
        "further investigation", "remains unclear", "not well understood",
        "poorly understood", "little is known", "requires more research",
        "warrants further study", "needs clarification", "unexplored",
        "understudied", "insufficient data", "limited evidence"
    ]

    topics = []
    stopwords = load_stopwords()

    for abstract in abstracts:
        lower_abstract = abstract.lower()
        for keyword in underexplored_keywords:
            if keyword in lower_abstract:
                # Extract context around the keyword
                start = lower_abstract.find(keyword)
                context = lower_abstract[max(0, start - 50):min(len(lower_abstract), start + 100)]
                # Extract potential topic words
                words = extract_keywords(context, stopwords, min_len=4)
                topics.extend(words[:3])

    topic_counter = Counter(topics)
    return topic_counter.most_common(10)


def _extract_future_directions(abstracts: List[str]) -> List[Tuple[str, int]]:
    """Extract suggested future research directions."""
    future_patterns = [
        r"future\s+(?:research|studies|work|investigation)[s]?\s+(?:should|could|may|might)\s+([^.]+)",
        r"(?:recommend|suggest)[s]?\s+(?:that\s+)?(?:future|further)\s+([^.]+)",
        r"further\s+research\s+(?:is\s+)?(?:needed|required|warranted)\s+(?:to|for)\s+([^.]+)",
        r"(?:should|could)\s+be\s+investigated\s+in\s+future\s+([^.]+)"
    ]

    all_directions = []

    for abstract in abstracts:
        lower_abstract = abstract.lower()
        for pattern in future_patterns:
            matches = re.findall(pattern, lower_abstract)
            if matches:
                all_directions.extend(matches)

    direction_counter = Counter(all_directions)
    # Filter meaningful directions
    filtered = [(dir, count) for dir, count in direction_counter.most_common(10)
                if len(dir) > 15]

    return filtered[:5]  # Top 5 future directions


def _generate_gap_summary(
    limitations: List[Tuple[str, int]],
    topics: List[Tuple[str, int]],
    directions: List[Tuple[str, int]]
) -> str:
    """Generate a structured summary of research gaps."""
    summary_parts = []

    if limitations:
        summary_parts.append(f"Identified {len(limitations)} recurring limitations across the literature.")

    if topics:
        summary_parts.append(f"Found {len(topics)} underexplored topics requiring further investigation.")

    if directions:
        summary_parts.append(f"Extracted {len(directions)} future research directions suggested by authors.")

    if not summary_parts:
        return "No significant research gaps detected in the analyzed literature."

    return " ".join(summary_parts)


def generate_gap_report(df: pd.DataFrame) -> str:
    """
    Generate a formatted text report of research gaps.

    Args:
        df: DataFrame with article data

    Returns:
        Formatted text report
    """
    gaps = detect_research_gaps(df)

    report = "=" * 60 + "\n"
    report += "RESEARCH GAP ANALYSIS REPORT\n"
    report += "=" * 60 + "\n\n"

    report += f"Total Articles Analyzed: {len(df)}\n\n"

    # Recurring Limitations
    report += "RECURRING LIMITATIONS:\n"
    report += "-" * 60 + "\n"
    for i, (limitation, freq) in enumerate(gaps["recurring_limitations"], 1):
        report += f"{i}. [{freq}x] {limitation}\n"
    report += "\n"

    # Underexplored Topics
    report += "UNDEREXPLORED TOPICS:\n"
    report += "-" * 60 + "\n"
    for i, (topic, freq) in enumerate(gaps["underexplored_topics"], 1):
        report += f"{i}. {topic} (mentioned {freq} times)\n"
    report += "\n"

    # Future Directions
    report += "FUTURE RESEARCH DIRECTIONS:\n"
    report += "-" * 60 + "\n"
    for i, (direction, freq) in enumerate(gaps["future_directions"], 1):
        report += f"{i}. [{freq}x] {direction}\n"
    report += "\n"

    # Summary
    report += "SUMMARY:\n"
    report += "-" * 60 + "\n"
    report += gaps["summary"] + "\n"
    report += "=" * 60 + "\n"

    logger.info("Gap report generated")
    return report