"""Pytest configuration and fixtures."""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../app/backend'))


@pytest.fixture
def sample_financial_data():
    """Sample financial data for testing."""
    return {
        'periods': ['2021', '2022', '2023'],
        'line_items': [
            {
                'code': 'REV_001',
                'label': 'Revenue',
                'values': {'2021': 1000000, '2022': 1200000, '2023': 1400000}
            },
            {
                'code': 'COGS_001',
                'label': 'Cost of Goods Sold',
                'values': {'2021': 600000, '2022': 700000, '2023': 800000}
            }
        ]
    }

