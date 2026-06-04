import pandas as pd
import pytest


# Test 1: Ensure duplicate customers are successfully dropped
def test_customer_deduplication():
    mock_rows = [
        {"customer id": 1, "customer name": "Alice"},
        {"customer id": 2, "customer name": "Bob"},
        {"customer id": 2, "customer name": "Bob"},
        {"customer id": 3, "customer name": "Charlie"}
    ]
    mock_data = pd.DataFrame(mock_rows)

    cleaned_df = mock_data.drop_duplicates(subset=['customer id'])

    assert len(cleaned_df) == 3
    assert cleaned_df['customer id'].duplicated().sum() == 0


# Test 2: Ensure rows with missing critical IDs are dropped
def test_drop_missing_critical_data():
    mock_rows = [
        {"id": 101, "customer id": 1, "books": "The Hobbit"},
        {"id": 102, "customer id": 2, "books": None},
        {"id": 103, "customer id": 3, "books": "1984"}
    ]
    mock_data = pd.DataFrame(mock_rows)

    cleaned_df = mock_data.dropna(subset=['id', 'customer id', 'books'])

    assert len(cleaned_df) == 2
    assert 102 not in cleaned_df['id'].values


# Test 3: Ensure dates are normalized correctly
def test_date_conversion():
    mock_rows = [
        {"book checkout": "2026-06-01"},
        {"book checkout": "not-a-date"}
    ]
    mock_data = pd.DataFrame(mock_rows)

    mock_data['book checkout'] = pd.to_datetime(mock_data['book checkout'], errors='coerce')

    # FIX: .iloc requires an index — .iloc[0] for the valid date, .iloc[1] for the invalid one
    assert isinstance(mock_data['book checkout'].iloc[0], pd.Timestamp)
    assert pd.isna(mock_data['book checkout'].iloc[1])