"""
Research Trend Analysis Module.
Detects emerging, stable, and declining research trends over time.
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple
from sklearn.feature_extraction.text import CountVectorizer
from scipy.stats import linregress
from datetime import datetime

logger = logging.getLogger(__name__)

class TrendDetector:
    """Detects momentum and bursts in research topics over time."""

    def __init__(self, min_df: int = 2):
        """
        Initialize the trend detector.
        
        Args:
            min_df: Minimum document frequency for a keyword to be considered.
        """
        self.min_df = min_df
        self.is_fitted = False
        self.df: Optional[pd.DataFrame] = None
        self.vectorizer = CountVectorizer(
            stop_words='english', 
            ngram_range=(1, 2), 
            min_df=self.min_df, 
            max_df=0.9
        )
        
        # Artifacts
        self.yearly_counts: Optional[pd.DataFrame] = None
        self.momentum_df: Optional[pd.DataFrame] = None

    def _extract_year(self, date_str: str) -> int:
        """Robustly extract a year from various date string formats."""
        try:
            if not isinstance(date_str, str):
                return datetime.now().year
            
            # Common PubMed format: '2023 Oct 15' or '2023'
            year_str = date_str.split()[0]
            if len(year_str) == 4 and year_str.isdigit():
                return int(year_str)
            
            # Fallback for YYYY/MM/DD
            if '/' in date_str:
                parts = date_str.split('/')
                for p in parts:
                    if len(p) == 4 and p.isdigit():
                        return int(p)
                        
            # Fallback for YYYY-MM-DD
            if '-' in date_str:
                parts = date_str.split('-')
                for p in parts:
                    if len(p) == 4 and p.isdigit():
                        return int(p)
                        
        except Exception as e:
            logger.debug(f"Could not parse year from '{date_str}': {e}")
            
        return datetime.now().year

    def fit(self, df: pd.DataFrame) -> bool:
        """
        Analyze the temporal distribution of keywords in the dataframe.
        
        Args:
            df: DataFrame containing 'pub_date', 'title', 'abstract'
            
        Returns:
            bool: Success status
        """
        if df is None or df.empty:
            logger.warning("Empty DataFrame provided to TrendDetector")
            return False
            
        if 'pub_date' not in df.columns:
            logger.error("DataFrame must contain 'pub_date' column")
            return False

        self.df = df.copy()
        
        # 1. Clean and extract years
        self.df['Year'] = self.df['pub_date'].apply(self._extract_year)
        
        # Check if we have enough temporal spread
        unique_years = self.df['Year'].nunique()
        if unique_years < 2:
            logger.warning("Need at least 2 distinct years to calculate trends. Current corpus spans 1 year.")
            # We can still fit, but momentum will be mostly 0
        
        # 2. Prepare text
        self.df['Text'] = self.df['title'].fillna('') + " " + self.df['abstract'].fillna('')
        
        try:
            # 3. Vectorize text to get document-term matrix
            dtm = self.vectorizer.fit_transform(self.df['Text'])
            feature_names = self.vectorizer.get_feature_names_out()
            
            # 4. Group by year
            # Create a dense representation for easier manipulation (safe if max_df/min_df are set)
            dtm_df = pd.DataFrame(dtm.toarray(), columns=feature_names)
            dtm_df['Year'] = self.df['Year'].values
            
            # Sum word occurrences per year
            self.yearly_counts = dtm_df.groupby('Year').sum()
            
            self.is_fitted = True
            logger.info(f"Fitted TrendDetector over {unique_years} years and {len(feature_names)} terms.")
            return True
            
        except Exception as e:
            logger.error(f"Error during trend fitting: {e}")
            self.is_fitted = False
            return False

    def calculate_momentum(self) -> pd.DataFrame:
        """
        Calculate the momentum (linear trend) of keywords over time.
        
        Returns:
            DataFrame sorted by Slope (momentum), containing trend categorizations.
        """
        if not self.is_fitted or self.yearly_counts is None:
            return pd.DataFrame()

        years = np.array(self.yearly_counts.index)
        
        if len(years) < 2:
            logger.warning("Insufficient time points for regression.")
            # Return a basic frequency count if only 1 year exists
            total_freq = self.yearly_counts.sum(axis=0)
            df = pd.DataFrame({'Total_Frequency': total_freq})
            df['Slope'] = 0.0
            df['Trend'] = 'Stable'
            return df.sort_values('Total_Frequency', ascending=False)

        results = []
        
        # Normalize yearly counts to account for total publication volume per year
        # (Relative frequency prevents general volume increase from looking like specific topic growth)
        total_pubs_per_year = self.yearly_counts.sum(axis=1)
        normalized_counts = self.yearly_counts.div(total_pubs_per_year, axis=0).fillna(0) * 1000 # per 1000 words

        for term in self.yearly_counts.columns:
            # Absolute frequency
            total_freq = self.yearly_counts[term].sum()
            if total_freq < self.min_df:
                continue
                
            # Use normalized frequencies for regression
            y = normalized_counts[term].values
            
            # Linear regression: Slope indicates growth or decline
            slope, intercept, r_value, p_value, std_err = linregress(years, y)
            
            results.append({
                'Term': term,
                'Total_Frequency': int(total_freq),
                'Slope': float(slope),
                'R_squared': float(r_value**2)
            })

        df = pd.DataFrame(results)
        
        if df.empty:
            return df

        # Categorize trends
        # Use percentiles or fixed thresholds to categorize
        slope_std = df['Slope'].std()
        slope_mean = df['Slope'].mean()
        
        conditions = [
            (df['Slope'] > slope_mean + slope_std),  # Fast growth
            (df['Slope'] < slope_mean - slope_std)   # Fast decline
        ]
        choices = ['Emerging 🚀', 'Declining 📉']
        df['Trend'] = np.select(conditions, choices, default='Stable ➡️')
        
        self.momentum_df = df.sort_values('Slope', ascending=False)
        return self.momentum_df

    def get_burst_keywords(self) -> List[str]:
        """
        Identify keywords that have experienced a sudden spike in the most recent year.
        
        Returns:
            List of burst keywords.
        """
        if not self.is_fitted or self.yearly_counts is None:
            return []
            
        years = sorted(self.yearly_counts.index)
        if len(years) < 2:
            return []
            
        current_year = years[-1]
        previous_years = years[:-1]
        
        bursts = []
        for term in self.yearly_counts.columns:
            current_val = self.yearly_counts.loc[current_year, term]
            if current_val < 3: # Ignore low-volume noise
                continue
                
            historical_max = self.yearly_counts.loc[previous_years, term].max()
            historical_mean = self.yearly_counts.loc[previous_years, term].mean()
            
            # Burst definition: Current year is more than double the historical max, 
            # and significantly above the mean
            if current_val > historical_max * 2 and current_val > historical_mean * 3:
                bursts.append(term)
                
        return bursts
        
    def get_timeline_data(self, terms: List[str]) -> pd.DataFrame:
        """
        Get absolute frequency counts for specific terms over time, useful for plotting.
        """
        if not self.is_fitted or self.yearly_counts is None:
            return pd.DataFrame()
            
        valid_terms = [t for t in terms if t in self.yearly_counts.columns]
        if not valid_terms:
            return pd.DataFrame()
            
        return self.yearly_counts[valid_terms].reset_index()