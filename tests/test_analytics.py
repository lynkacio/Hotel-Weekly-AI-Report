import pandas as pd
from src.analytics import assess_hotels
from main import previous_iso_week
from datetime import date

def test_classification_and_zero_orders():
    df = pd.DataFrame([
        {'brandname':'A','revenue':100,'Order':0,'Boss Gmail':'a@example.com'},
        {'brandname':'B','revenue':200,'Order':2,'Boss Gmail':'b@example.com'},
        {'brandname':'C','revenue':300,'Order':3,'Boss Gmail':'c@example.com'},
    ])
    out = assess_hotels(df)
    assert [x['classification'] for x in out] == ['Needs Improvement','Doing Well','Doing Well']
    assert out[0]['aov'] is None

def test_year_boundary():
    assert previous_iso_week(date(2026,1,5)) == '2026-W01'
