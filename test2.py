import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from main import enrich_dateDuration, filter_valid_loans

def test_enrich_dateDuration():
    
    input_df = pd.DataFrame({
        'Book checkout': pd.to_datetime(['2026-01-01', '2026-02-15', '2026-03-10']),
        'Book Returned': pd.to_datetime(['2026-01-10', '2026-02-20', '2026-03-05'])
    })
    result_df = enrich_dateDuration(input_df, colA='Book Returned', colB='Book checkout')
    
    expected_df = pd.DataFrame({
        'Book checkout': pd.to_datetime(['2026-01-01', '2026-02-15', '2026-03-10']),
        'Book Returned': pd.to_datetime(['2026-01-10', '2026-02-20', '2026-03-05']),
        'loan_duration': [9, 5, -5],
        'Checkout_Month': ['January', 'February', 'March']
    })
    
    assert_frame_equal(result_df, expected_df)

def test_filter_valid_loans():
    
    input_df = pd.DataFrame({
        'Customer ID': [1, 3, 7],
        'loan_duration': [12, -2, 0]
    })
    
    result_df, drop_count = filter_valid_loans(input_df)


    expected_df = pd.DataFrame({
        'Customer ID': [1, 3],
        'loan_duration': [12, -2]
    }, index=[0, 1])
    
    assert_frame_equal(result_df, expected_df)
    
    assert drop_count == 1