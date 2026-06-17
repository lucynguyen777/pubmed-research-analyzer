# Phase 4: Research Trend Detection Specification

## Overview
Adds predictive analytics and temporal analysis to the platform. By analyzing publication metadata (years, topics, keywords) across time, the tool will identify accelerating vs. decelerating research topics. This turns static data into strategic insights, allowing researchers to see where the field is heading.

## 1. Directory Structure Updates
```
app/
├── intelligence/
│   ├── trend_analysis.py   # New module
```

## 2. Module Specifications

### `app/intelligence/trend_analysis.py`
**Class: `TrendDetector`**
- `__init__()`: Initializes the detector.
- `fit(df: pd.DataFrame)`: 
  1. Validates presence of `pub_date` and text fields.
  2. Parses dates into standard formats.
  3. Extracts bigrams/trigrams across the timeline.
- `calculate_momentum() -> pd.DataFrame`: 
  1. Groups keywords/topics by year.
  2. Calculates the Compound Annual Growth Rate (CAGR) or linear regression slope of keyword frequency.
  3. Returns a DataFrame of trends sorted by momentum (Emerging, Stable, Declining).
- `get_burst_keywords() -> List[str]`: Identifies keywords that have seen a sudden, sharp spike in the most recent years.

## 3. Dashboard Integration
In `dashboard/streamlit_app.py`:
- Update `display_analytics` or add a new tab: "📈 Trend Detection".
- Include a line chart showing the frequency of the top 3 "Emerging" keywords over time.
- Display a categorized table: 🚀 Emerging Trends, 📉 Declining Trends.

## 4. Testing Strategy
- `tests/test_intelligence/test_trend_analysis.py`
- Create a mock dataframe spanning 5 years.
- Artificially insert a keyword ("mRNA") that grows from 0 to 10 mentions.
- Assert that `calculate_momentum()` flags "mRNA" as an emerging/high-momentum trend.

## 5. Implementation Steps
1. Create `TrendDetector` class using `pandas` and basic statistics (e.g., `scipy.stats.linregress`).
2. Write unit tests.
3. Integrate into Streamlit UI.
4. Verify end-to-end functionality.
