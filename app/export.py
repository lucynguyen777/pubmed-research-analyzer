"""
Export functionality for articles and analysis results.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
from pathlib import Path
import logging
from app.config import EXPORTS_DIR

logger = logging.getLogger(__name__)


def export_csv(df: pd.DataFrame, filename: str = "articles.csv") -> str:
    """
    Export DataFrame to CSV file.

    Args:
        df: DataFrame to export
        filename: Output filename

    Returns:
        Path to exported file
    """
    if df.empty:
        logger.warning("Empty DataFrame provided for CSV export")
        return ""

    try:
        filepath = EXPORTS_DIR / filename
        df.to_csv(filepath, index=False, encoding="utf-8")
        logger.info(f"CSV exported to {filepath}")
        return str(filepath)
    except Exception as exc:
        logger.error(f"CSV export failed: {exc}")
        raise


def export_excel(df: pd.DataFrame, filename: str = "articles.xlsx") -> str:
    """
    Export DataFrame to Excel file.

    Args:
        df: DataFrame to export
        filename: Output filename

    Returns:
        Path to exported file
    """
    if df.empty:
        logger.warning("Empty DataFrame provided for Excel export")
        return ""

    try:
        filepath = EXPORTS_DIR / filename
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Articles", index=False)

        logger.info(f"Excel exported to {filepath}")
        return str(filepath)
    except Exception as exc:
        logger.error(f"Excel export failed: {exc}")
        raise


def export_analytics(
    analytics: Dict[str, Any],
    filename: str = "analytics.xlsx"
) -> str:
    """
    Export analytics results to Excel with multiple sheets.

    Args:
        analytics: Dictionary with year_counts, journal_counts, author_counts, keyword_counts
        filename: Output filename

    Returns:
        Path to exported file
    """
    if not analytics:
        logger.warning("Empty analytics provided for export")
        return ""

    try:
        filepath = EXPORTS_DIR / filename

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            # Publications per year
            year_df = pd.DataFrame(
                list(analytics.get("year_counts", {}).items()),
                columns=["Year", "Count"]
            )
            year_df.to_excel(writer, sheet_name="Publications per Year", index=False)

            # Top journals
            journal_df = pd.DataFrame(
                list(analytics.get("journal_counts", {}).items()),
                columns=["Journal", "Count"]
            )
            journal_df.to_excel(writer, sheet_name="Top Journals", index=False)

            # Top authors
            author_df = pd.DataFrame(
                list(analytics.get("author_counts", {}).items()),
                columns=["Author", "Count"]
            )
            author_df.to_excel(writer, sheet_name="Top Authors", index=False)

            # Keyword frequency
            keyword_df = pd.DataFrame(
                list(analytics.get("keyword_counts", {}).items()),
                columns=["Keyword", "Frequency"]
            )
            keyword_df.to_excel(writer, sheet_name="Keywords", index=False)

        logger.info(f"Analytics exported to {filepath}")
        return str(filepath)
    except Exception as exc:
        logger.error(f"Analytics export failed: {exc}")
        raise


def export_comparison_report(
    comparison_data: Dict[str, Any],
    filename: str = "comparison_report.xlsx"
) -> str:
    """
    Export literature comparison report to Excel.

    Args:
        comparison_data: Comparison data with methodology, findings, etc.
        filename: Output filename

    Returns:
        Path to exported file
    """
    if not comparison_data:
        logger.warning("Empty comparison data provided for export")
        return ""

    try:
        filepath = EXPORTS_DIR / filename

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            for sheet_name, data in comparison_data.items():
                if isinstance(data, pd.DataFrame):
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
                elif isinstance(data, dict):
                    df = pd.DataFrame([data])
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"Comparison report exported to {filepath}")
        return str(filepath)
    except Exception as exc:
        logger.error(f"Comparison export failed: {exc}")
        raise


def export_research_gap_report(
    gap_report: Dict[str, Any],
    filename: str = "research_gaps.xlsx"
) -> str:
    """
    Export research gap analysis report to Excel.

    Args:
        gap_report: Research gap analysis data
        filename: Output filename

    Returns:
        Path to exported file
    """
    if not gap_report:
        logger.warning("Empty gap report provided for export")
        return ""

    try:
        filepath = EXPORTS_DIR / filename

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            # Recurring limitations
            limitations_df = pd.DataFrame(
                gap_report.get("recurring_limitations", []),
                columns=["Limitation", "Frequency"]
            )
            limitations_df.to_excel(
                writer, sheet_name="Recurring Limitations", index=False
            )

            # Underexplored topics
            topics_df = pd.DataFrame(
                gap_report.get("underexplored_topics", []),
                columns=["Topic", "Mention Count"]
            )
            topics_df.to_excel(writer, sheet_name="Underexplored Topics", index=False)

            # Future directions
            directions_df = pd.DataFrame(
                gap_report.get("future_directions", []),
                columns=["Direction", "Frequency"]
            )
            directions_df.to_excel(
                writer, sheet_name="Future Directions", index=False
            )

        logger.info(f"Research gap report exported to {filepath}")
        return str(filepath)
    except Exception as exc:
        logger.error(f"Gap report export failed: {exc}")
        raise


def get_export_dir() -> str:
    """Get exports directory path."""
    return str(EXPORTS_DIR)


def list_exports() -> List[str]:
    """List all exported files."""
    if not EXPORTS_DIR.exists():
        return []

    exports = [f.name for f in EXPORTS_DIR.glob("*")]
    logger.info(f"Found {len(exports)} export files")
    return exports