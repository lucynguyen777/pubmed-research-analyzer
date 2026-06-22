import pytest
import pandas as pd
from app.intelligence.trend_analysis import TrendDetector

@pytest.fixture
def mock_timeline_df():
    # Construct a dataset where 'vaccine' rises, 'chloroquine' falls, and 'placebo' is stable
    data = []
    # 2020: 3 chloroquine, 1 vaccine, 2 placebo
    data.extend([
        {'pub_date': '2020/01/01', 'title': 'chloroquine efficacy', 'abstract': 'Study on chloroquine and placebo'},
        {'pub_date': '2020/05/12', 'title': 'chloroquine treatment', 'abstract': 'Using chloroquine vs placebo'},
        {'pub_date': '2020/09/20', 'title': 'chloroquine virus', 'abstract': 'Does chloroquine work?'},
        {'pub_date': '2020/12/30', 'title': 'vaccine trials', 'abstract': 'First trials of vaccine candidates'}
    ])
    # 2021: 2 chloroquine, 3 vaccine, 2 placebo
    data.extend([
        {'pub_date': '2021/02/01', 'title': 'vaccine efficacy', 'abstract': 'Study on vaccine and placebo'},
        {'pub_date': '2021/04/15', 'title': 'vaccine safety', 'abstract': 'Safety profile of vaccine'},
        {'pub_date': '2021/07/20', 'title': 'chloroquine failure', 'abstract': 'chloroquine shows no benefit vs placebo'},
        {'pub_date': '2021/10/10', 'title': 'vaccine rollout', 'abstract': 'Rollout of the vaccine'},
        {'pub_date': '2021/11/15', 'title': 'chloroquine study', 'abstract': 'Another study on chloroquine'}
    ])
    # 2022: 0 chloroquine, 6 vaccine, 2 placebo
    data.extend([
        {'pub_date': '2022/01/10', 'title': 'vaccine booster', 'abstract': 'booster vaccine efficacy with placebo'},
        {'pub_date': '2022/03/15', 'title': 'vaccine mandate', 'abstract': 'mandate for vaccine dose'},
        {'pub_date': '2022/05/20', 'title': 'vaccine response', 'abstract': 'immune response of vaccine'},
        {'pub_date': '2022/07/22', 'title': 'booster vaccine', 'abstract': 'booster vaccine vs placebo'},
        {'pub_date': '2022/09/05', 'title': 'vaccine variant', 'abstract': 'vaccine efficacy against variant'},
        {'pub_date': '2022/11/18', 'title': 'vaccine update', 'abstract': 'update vaccine formulation'}
    ])
    return pd.DataFrame(data)

def test_trend_detector_init():
    detector = TrendDetector()
    assert not detector.is_fitted
    assert detector.min_df == 2

def test_trend_detector_empty():
    detector = TrendDetector()
    assert detector.fit(pd.DataFrame()) == False
    assert detector.fit(None) == False  # type: ignore[arg-type]

def test_trend_detector_fit_and_momentum(mock_timeline_df):
    detector = TrendDetector(min_df=2)
    success = detector.fit(mock_timeline_df)
    assert success
    assert detector.is_fitted
    assert detector.df is not None
    
    # Verify year extraction
    assert set(detector.df['Year'].unique()) == {2020, 2021, 2022}
    
    momentum = detector.calculate_momentum()
    assert not momentum.empty
    
    # 'vaccine' should be recognized as growing/Emerging
    vaccine_row = momentum[momentum['Term'] == 'vaccine']
    assert not vaccine_row.empty
    assert vaccine_row.iloc[0]['Slope'] > 0
    
    # 'chloroquine' should be declining
    chloroquine_row = momentum[momentum['Term'] == 'chloroquine']
    assert not chloroquine_row.empty
    assert chloroquine_row.iloc[0]['Slope'] < 0

def test_get_timeline_data(mock_timeline_df):
    detector = TrendDetector(min_df=2)
    detector.fit(mock_timeline_df)
    
    timeline = detector.get_timeline_data(['vaccine', 'chloroquine'])
    assert 'Year' in timeline.columns
    assert 'vaccine' in timeline.columns
    assert 'chloroquine' in timeline.columns
    assert len(timeline) == 3 # 3 years
