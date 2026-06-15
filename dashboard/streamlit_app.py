"""
Streamlit Dashboard for PubMed Research Analyzer.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.search import search_pubmed
from app.fetch import fetch_articles_batch
from app.analyze import analyze_publications
from app.export import export_csv, export_excel, export_analytics, export_comparison_report, export_research_gap_report
from app.summarize import summarize_abstract
from app.research_gap import detect_research_gaps, generate_gap_report
from app.literature_comparison import compare_articles, generate_comparison_report
from app.config import NCBI_EMAIL, MAX_RESULTS_DEFAULT

st.set_page_config(page_title="PubMed Research Analyzer", layout="wide", page_icon="🔬")

# Initialize session state
if "articles_df" not in st.session_state:
    st.session_state.articles_df = pd.DataFrame()
if "analytics" not in st.session_state:
    st.session_state.analytics = {}


def main():
    """Main dashboard application."""
    st.title("🔬 PubMed Research Analyzer")
    st.markdown("*Analyze scientific literature with AI-powered insights*")

    # Sidebar
    with st.sidebar:
        st.header("Search Parameters")
        
        query = st.text_input("Search Query", placeholder="e.g., COVID-19 vaccine")
        max_results = st.slider("Maximum Results", min_value=5, max_value=100, value=MAX_RESULTS_DEFAULT)
        
        search_type = st.selectbox("Search Type", ["Keyword", "Author", "Journal"])
        
        with st.expander("Advanced Filters"):
            date_from = st.text_input("Date From (YYYY/MM/DD)", placeholder="2020/01/01")
            date_to = st.text_input("Date To (YYYY/MM/DD)", placeholder="2024/12/31")
        
        search_button = st.button("🔍 Search PubMed", type="primary", use_container_width=True)
        
        st.divider()
        st.markdown(f"**NCBI Email:** {NCBI_EMAIL}")
        st.caption("Configure in .env file")

    # Main content
    if search_button and query:
        with st.spinner("Searching PubMed..."):
            try:
                pmids = search_pubmed(query, max_results, date_from if date_from else None, date_to if date_to else None)
                
                if not pmids:
                    st.warning("No articles found. Try a different query.")
                    return
                
                st.success(f"Found {len(pmids)} articles")
                
                with st.spinner("Fetching article details..."):
                    st.session_state.articles_df = fetch_articles_batch(pmids)
                    
                with st.spinner("Analyzing publications..."):
                    st.session_state.analytics = analyze_publications(st.session_state.articles_df)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                return

    # Display results if available
    if not st.session_state.articles_df.empty:
        tabs = st.tabs(["📊 Overview", "📈 Analytics", "🔍 Research Gaps", "⚖️ Comparison", "💾 Export"])
        
        with tabs[0]:
            display_overview()
        
        with tabs[1]:
            display_analytics()
        
        with tabs[2]:
            display_research_gaps()
        
        with tabs[3]:
            display_comparison()
        
        with tabs[4]:
            display_export_options()


def display_overview():
    """Display articles overview."""
    st.header("Articles Overview")
    
    df = st.session_state.articles_df
    st.metric("Total Articles", len(df))
    
    # Display table
    display_df = df[["pmid", "title", "journal", "pub_date"]].copy()
    st.dataframe(display_df, use_container_width=True, height=400)
    
    # Article details expander
    with st.expander("View Article Details"):
        selected_pmid = st.selectbox("Select Article", df["pmid"].tolist())
        article = df[df["pmid"] == selected_pmid].iloc[0]
        
        st.subheader(article["title"])
        st.write(f"**PMID:** {article['pmid']}")
        st.write(f"**Journal:** {article['journal']}")
        st.write(f"**Date:** {article['pub_date']}")
        st.write(f"**DOI:** {article['doi']}")
        
        if article["authors"]:
            st.write(f"**Authors:** {', '.join(article['authors'][:5])}")
        
        st.write("**Abstract:**")
        st.write(article["abstract"])


def display_analytics():
    """Display analytics visualizations."""
    st.header("Research Analytics")
    
    analytics = st.session_state.analytics
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Publications per Year")
        if analytics.get("year_counts"):
            fig = px.bar(
                x=list(analytics["year_counts"].keys()),
                y=list(analytics["year_counts"].values()),
                labels={"x": "Year", "y": "Count"},
                title="Publication Timeline"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No year data available")
    
    with col2:
        st.subheader("Top Journals")
        if analytics.get("journal_counts"):
            fig = px.bar(
                x=list(analytics["journal_counts"].values()),
                y=list(analytics["journal_counts"].keys()),
                orientation="h",
                labels={"x": "Count", "y": "Journal"},
                title="Most Frequent Journals"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No journal data available")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Top Authors")
        if analytics.get("author_counts"):
            author_df = pd.DataFrame(
                list(analytics["author_counts"].items()),
                columns=["Author", "Publications"]
            )
            st.dataframe(author_df, use_container_width=True)
        else:
            st.info("No author data available")
    
    with col4:
        st.subheader("Keyword Frequency")
        if analytics.get("keyword_counts"):
            keywords = list(analytics["keyword_counts"].items())[:15]
            fig = px.bar(
                x=[k[1] for k in keywords],
                y=[k[0] for k in keywords],
                orientation="h",
                labels={"x": "Frequency", "y": "Keyword"}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No keyword data available")


def display_research_gaps():
    """Display research gap analysis."""
    st.header("Research Gap Analysis")
    
    if st.button("🔬 Analyze Research Gaps"):
        with st.spinner("Analyzing research gaps..."):
            gaps = detect_research_gaps(st.session_state.articles_df)
            
            st.subheader("Summary")
            st.info(gaps["summary"])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Recurring Limitations", len(gaps["recurring_limitations"]))
            with col2:
                st.metric("Underexplored Topics", len(gaps["underexplored_topics"]))
            with col3:
                st.metric("Future Directions", len(gaps["future_directions"]))
            
            st.subheader("Recurring Limitations")
            if gaps["recurring_limitations"]:
                for i, (lim, freq) in enumerate(gaps["recurring_limitations"], 1):
                    st.write(f"{i}. **[{freq}x]** {lim}")
            else:
                st.info("No recurring limitations detected")
            
            st.subheader("Underexplored Topics")
            if gaps["underexplored_topics"]:
                topics_df = pd.DataFrame(gaps["underexplored_topics"], columns=["Topic", "Frequency"])
                st.dataframe(topics_df, use_container_width=True)
            else:
                st.info("No underexplored topics detected")
            
            st.subheader("Future Research Directions")
            if gaps["future_directions"]:
                for i, (dir, freq) in enumerate(gaps["future_directions"], 1):
                    st.write(f"{i}. **[{freq}x]** {dir}")
            else:
                st.info("No future directions found")


def display_comparison():
    """Display literature comparison."""
    st.header("Literature Comparison")
    
    df = st.session_state.articles_df
    selected_pmids = st.multiselect("Select Articles to Compare", df["pmid"].tolist(), max_selections=5)
    
    if selected_pmids and st.button("⚖️ Compare Articles"):
        with st.spinner("Comparing articles..."):
            comparison = compare_articles(df, selected_pmids)
            
            st.subheader("Overview Comparison")
            st.dataframe(comparison["overview"], use_container_width=True)
            
            st.subheader("Methodology Comparison")
            st.dataframe(comparison["methodology"], use_container_width=True)
            
            st.subheader("Key Findings")
            st.dataframe(comparison["findings"], use_container_width=True)
            
            st.subheader("Limitations")
            st.dataframe(comparison["limitations"], use_container_width=True)


def display_export_options():
    """Display export options."""
    st.header("Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Export Articles (CSV)", use_container_width=True):
            try:
                filepath = export_csv(st.session_state.articles_df)
                st.success(f"Exported to {filepath}")
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
        
        if st.button("📊 Export Articles (Excel)", use_container_width=True):
            try:
                filepath = export_excel(st.session_state.articles_df)
                st.success(f"Exported to {filepath}")
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
    
    with col2:
        if st.button("📈 Export Analytics", use_container_width=True):
            try:
                filepath = export_analytics(st.session_state.analytics)
                st.success(f"Exported to {filepath}")
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
        
        if st.button("🔬 Export Research Gaps", use_container_width=True):
            try:
                gaps = detect_research_gaps(st.session_state.articles_df)
                filepath = export_research_gap_report(gaps)
                st.success(f"Exported to {filepath}")
            except Exception as e:
                st.error(f"Export failed: {str(e)}")


if __name__ == "__main__":
    main()