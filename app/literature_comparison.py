"""
Literature Comparison Module - Compares multiple PubMed articles.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import logging
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


def compare_articles(df: pd.DataFrame, pmids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Compare multiple articles across different dimensions.

    Args:
        df: DataFrame with article data
        pmids: Optional list of specific PMIDs to compare (compares all if None)

    Returns:
        Dictionary with comparison tables and analysis
    """
    if df.empty:
        logger.warning("Empty DataFrame provided for comparison")
        return {
            "overview": pd.DataFrame(),
            "methodology": pd.DataFrame(),
            "findings": pd.DataFrame(),
            "limitations": pd.DataFrame()
        }

    # Filter by specific PMIDs if provided
    if pmids:
        df = df[df["pmid"].isin(pmids)]

    if df.empty:
        logger.warning("No articles found for comparison")
        return {
            "overview": pd.DataFrame(),
            "methodology": pd.DataFrame(),
            "findings": pd.DataFrame(),
            "limitations": pd.DataFrame()
        }

    # Generate comparison tables
    overview = _generate_overview_comparison(df)
    methodology = _extract_methodology_comparison(df)
    findings = _extract_findings_comparison(df)
    limitations = _extract_limitations_comparison(df)

    logger.info(f"Compared {len(df)} articles")
    return {
        "overview": overview,
        "methodology": methodology,
        "findings": findings,
        "limitations": limitations
    }


def _generate_overview_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Generate overview comparison table."""
    comparison_data = []

    for _, row in df.iterrows():
        # Extract sample size if mentioned in abstract
        sample_size = _extract_sample_size(row.get("abstract", ""))

        comparison_data.append({
            "PMID": row.get("pmid", "N/A"),
            "Title": row.get("title", "N/A")[:80] + "..." if len(str(row.get("title", ""))) > 80 else row.get("title", "N/A"),
            "Year": str(row.get("pub_date", "N/A")).split("-")[0],
            "Journal": row.get("journal", "N/A"),
            "Authors": len(row.get("authors", [])),
            "Sample Size": sample_size
        })

    return pd.DataFrame(comparison_data)


def _extract_sample_size(abstract: str) -> str:
    """Extract sample size from abstract text."""
    if not abstract or abstract == "N/A":
        return "Not specified"

    # Common patterns for sample size
    patterns = [
        r"(\d+)\s+(?:patients|participants|subjects|individuals|samples)",
        r"n\s*=\s*(\d+)",
        r"sample\s+size\s+of\s+(\d+)",
        r"total\s+of\s+(\d+)\s+(?:patients|participants)"
    ]

    for pattern in patterns:
        match = re.search(pattern, abstract.lower())
        if match:
            return match.group(1)

    return "Not specified"


def _extract_methodology_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Extract and compare methodologies."""
    methodology_data = []

    methodology_keywords = {
        "randomized": ["randomized", "randomised", "rct"],
        "observational": ["observational", "cohort", "case-control"],
        "meta-analysis": ["meta-analysis", "systematic review"],
        "experimental": ["experimental", "laboratory", "in vitro", "in vivo"],
        "qualitative": ["qualitative", "interview", "survey"],
        "quantitative": ["quantitative", "statistical"]
    }

    for _, row in df.iterrows():
        abstract = str(row.get("abstract", "")).lower()
        title = str(row.get("title", "")).lower()
        combined = abstract + " " + title

        methods = []
        for method_type, keywords in methodology_keywords.items():
            if any(keyword in combined for keyword in keywords):
                methods.append(method_type)

        methodology_data.append({
            "PMID": row.get("pmid", "N/A"),
            "Study Type": ", ".join(methods) if methods else "Not specified",
            "Sample Size": _extract_sample_size(abstract),
            "Duration": _extract_study_duration(abstract)
        })

    return pd.DataFrame(methodology_data)


def _extract_study_duration(abstract: str) -> str:
    """Extract study duration from abstract."""
    if not abstract or abstract == "N/A":
        return "Not specified"

    patterns = [
        r"(\d+)\s+(?:months|years|weeks|days)",
        r"between\s+(\d{4})\s+and\s+(\d{4})",
        r"from\s+(\d{4})\s+to\s+(\d{4})"
    ]

    for pattern in patterns:
        match = re.search(pattern, abstract.lower())
        if match:
            return match.group(0)

    return "Not specified"


def _extract_findings_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Extract and compare key findings."""
    findings_data = []

    finding_keywords = [
        "found", "showed", "demonstrated", "revealed", "concluded",
        "results indicate", "significant", "associated with"
    ]

    for _, row in df.iterrows():
        abstract = str(row.get("abstract", ""))

        # Extract sentences with findings
        findings = []
        sentences = abstract.split(".")
        for sentence in sentences:
            lower_sent = sentence.lower()
            if any(keyword in lower_sent for keyword in finding_keywords):
                findings.append(sentence.strip())

        # Get first 2 findings
        main_findings = findings[:2] if findings else ["No clear findings extracted"]

        findings_data.append({
            "PMID": row.get("pmid", "N/A"),
            "Title": row.get("title", "N/A")[:60] + "..." if len(str(row.get("title", ""))) > 60 else row.get("title", "N/A"),
            "Key Finding 1": main_findings[0][:150] + "..." if len(main_findings[0]) > 150 else main_findings[0],
            "Key Finding 2": main_findings[1][:150] + "..." if len(main_findings) > 1 and len(main_findings[1]) > 150 else (main_findings[1] if len(main_findings) > 1 else "N/A")
        })

    return pd.DataFrame(findings_data)


def _extract_limitations_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Extract and compare limitations."""
    limitations_data = []

    limitation_keywords = [
        "limitation", "limited by", "however", "despite",
        "small sample", "further research needed"
    ]

    for _, row in df.iterrows():
        abstract = str(row.get("abstract", ""))

        # Extract sentences with limitations
        limitations = []
        sentences = abstract.split(".")
        for sentence in sentences:
            lower_sent = sentence.lower()
            if any(keyword in lower_sent for keyword in limitation_keywords):
                limitations.append(sentence.strip())

        main_limitations = limitations[:2] if limitations else ["No limitations mentioned"]

        limitations_data.append({
            "PMID": row.get("pmid", "N/A"),
            "Title": row.get("title", "N/A")[:60] + "..." if len(str(row.get("title", ""))) > 60 else row.get("title", "N/A"),
            "Limitation 1": main_limitations[0][:150] + "..." if len(main_limitations[0]) > 150 else main_limitations[0],
            "Limitation 2": main_limitations[1][:150] + "..." if len(main_limitations) > 1 and len(main_limitations[1]) > 150 else (main_limitations[1] if len(main_limitations) > 1 else "N/A")
        })

    return pd.DataFrame(limitations_data)


def generate_comparison_report(df: pd.DataFrame, pmids: Optional[List[str]] = None) -> str:
    """
    Generate a formatted text report comparing articles.

    Args:
        df: DataFrame with article data
        pmids: Optional list of specific PMIDs to compare

    Returns:
        Formatted text report
    """
    comparison = compare_articles(df, pmids)

    report = "=" * 80 + "\n"
    report += "LITERATURE COMPARISON REPORT\n"
    report += "=" * 80 + "\n\n"

    report += f"Total Articles Compared: {len(comparison['overview'])}\n\n"

    # Overview
    report += "OVERVIEW COMPARISON:\n"
    report += "-" * 80 + "\n"
    report += comparison["overview"].to_string(index=False) + "\n\n"

    # Methodology
    report += "METHODOLOGY COMPARISON:\n"
    report += "-" * 80 + "\n"
    report += comparison["methodology"].to_string(index=False) + "\n\n"

    # Findings
    report += "KEY FINDINGS COMPARISON:\n"
    report += "-" * 80 + "\n"
    report += comparison["findings"].to_string(index=False) + "\n\n"

    # Limitations
    report += "LIMITATIONS COMPARISON:\n"
    report += "-" * 80 + "\n"
    report += comparison["limitations"].to_string(index=False) + "\n\n"

    report += "=" * 80 + "\n"

    logger.info("Comparison report generated")
    return report