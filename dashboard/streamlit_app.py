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
from app.intelligence.citation_network import (
    CitationNetworkBuilder,
    NetworkAnalyzer,
    NetworkVisualizer,
)
from app.intelligence.semantic_search import SemanticSearchEngine
from app.export import export_influential_papers, export_citation_network

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
        tabs = st.tabs(["📊 Overview", "📈 Analytics", "🔍 Research Gaps", "⚖️ Comparison", "�️ Citation Network", "�💾 Export"])
        
        with tabs[0]:
            display_overview()
        
        with tabs[1]:
            display_analytics()
        
        with tabs[2]:
            display_research_gaps()
        
        with tabs[3]:
            display_comparison()
        
        with tabs[4]:
            display_citation_network()
        
        with tabs[5]:
            display_export_options()


def display_overview():
    """Display articles overview."""
    st.header("Articles Overview")
    
    df = st.session_state.articles_df
    
    # Initialize Semantic Search Engine in session state
    if "semantic_engine" not in st.session_state:
        st.session_state.semantic_engine = SemanticSearchEngine()
        
    if not st.session_state.semantic_engine.is_ready:
        with st.spinner("Building semantic search index..."):
            st.session_state.semantic_engine.build_index(df)

    # Top layout: Search & Metrics
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Semantic Search (Local Corpus)")
        semantic_query = st.text_input("Search current articles by concept/meaning:", placeholder="e.g. mRNA delivery mechanisms")
        
    with col2:
        st.metric("Total Articles", len(df))
        
    if semantic_query:
        search_results = st.session_state.semantic_engine.search(semantic_query, top_k=5)
        if not search_results.empty:
            st.markdown("##### Top Semantic Matches")
            for _, row in search_results.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['title']}** (Score: {row['similarity_score']:.3f})")
                    st.caption(f"PMID: {row['pmid']} | Journal: {row['journal']} | Date: {row['pub_date']}")
        else:
            st.info("No strong semantic matches found.")
    else:
        # Display default table when no semantic query
        display_df = df[["pmid", "title", "journal", "pub_date"]].copy()
        st.dataframe(display_df, use_container_width=True, height=400)
    
    st.divider()
    
    # Article details expander with similar papers
    with st.expander("View Article Details & Similar Papers"):
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
        
        # Display Similar Papers
        st.markdown("#### Similar Papers in Corpus")
        if st.button("Find Similar Papers"):
            similar_df = st.session_state.semantic_engine.find_similar_papers(selected_pmid, top_k=3)
            if not similar_df.empty:
                for _, sim_row in similar_df.iterrows():
                    st.markdown(f"- **[{sim_row['pmid']}]** {sim_row['title']} *(Sim: {sim_row['similarity_score']:.2f})*")
            else:
                st.info("No similar papers found in current corpus.")


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


def display_citation_network():
    """Display interactive citation network and analysis."""
    st.header("Citation Network Intelligence")
    st.markdown("Build and analyze citation networks to discover influential papers and research communities.")

    df = st.session_state.articles_df
    seed_pmids = df["pmid"].tolist()

    if "network_data" not in st.session_state:
        st.session_state.network_data = None

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Network Settings")
        max_seeds = st.number_input("Max seed papers", min_value=1, max_value=50, value=10)
        layout = st.selectbox("Layout Algorithm", ["spring", "kamada_kawai", "circular"])
        color_by = st.selectbox("Color By", ["pagerank", "betweenness", "closeness"])
        size_by = st.selectbox("Size By", ["in_degree", "total_degree", "pagerank"])

        if st.button("🕸️ Build Network", type="primary", use_container_width=True):
            with st.spinner("Fetching citation data & building network..."):
                builder = CitationNetworkBuilder()
                builder.build_network(seed_pmids[:max_seeds])
                
                analyzer = NetworkAnalyzer(builder.graph)
                analyzer.calculate_all_metrics()
                communities = analyzer.detect_communities()
                
                st.session_state.network_data = {
                    "graph": builder.graph,
                    "metrics": analyzer.metrics,
                    "communities": communities,
                    "stats": builder.get_network_stats(),
                    "influential": analyzer.identify_influential_papers()
                }

    with col2:
        if st.session_state.network_data:
            data = st.session_state.network_data
            
            # Display stats
            stats_cols = st.columns(4)
            stats = data["stats"]
            stats_cols[0].metric("Papers in Network", stats.get("Papers in network", 0))
            stats_cols[1].metric("Citation Links", stats.get("Citation links", 0))
            stats_cols[2].metric("Density", stats.get("Network density", "0"))
            stats_cols[3].metric("Connected Components", stats.get("Largest component", 0))

            st.divider()

            # Display interactive graph
            st.subheader("Interactive Citation Graph")
            visualizer = NetworkVisualizer(data["graph"], data["metrics"])
            
            fig_network = visualizer.generate_interactive_network(
                layout=layout,
                color_by=color_by,
                node_size_metric=size_by,
                max_nodes=150
            )
            st.plotly_chart(fig_network, use_container_width=True)

            st.divider()
            
            # Influence charts
            st.subheader("Influence & Communities")
            c1, c2 = st.columns(2)
            
            with c1:
                fig_influence = visualizer.generate_influence_chart(top_n=10)
                st.plotly_chart(fig_influence, use_container_width=True)
                
            with c2:
                if data["communities"]:
                    fig_community = visualizer.generate_community_chart(data["communities"])
                    st.plotly_chart(fig_community, use_container_width=True)
                else:
                    st.info("Community detection requires python-louvain package.")
        else:
            st.info("Click 'Build Network' to generate the citation graph.")

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