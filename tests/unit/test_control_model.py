"""Unit tests for the Control model."""

import pytest
from datetime import date, timedelta
from cmmc_tracker.app.models.control import Control
from cmmc_tracker.app.services.database import execute_query

@pytest.mark.unit
@pytest.mark.models
def test_control_creation():
    """Test creating a Control object."""
    control = Control(
        control_id='TEST.1.001',
        control_name='Test Control',
        control_description='This is a test control',
        nist_mapping='NIST.800.171.3.1.1',
        review_frequency='Annual',
        last_review_date='2023-01-01',
        next_review_date='2024-01-01'
    )
    
    assert control.control_id == 'TEST.1.001'
    assert control.control_name == 'Test Control'
    assert control.control_description == 'This is a test control'
    assert control.nist_mapping == 'NIST.800.171.3.1.1'
    assert control.review_frequency == 'Annual'
    assert control.last_review_date == '2023-01-01'
    assert control.next_review_date == '2024-01-01'

@pytest.mark.unit
@pytest.mark.models
def test_control_to_dict():
    """Test the to_dict method of the Control class."""
    control = Control(
        control_id='TEST.1.002',
        control_name='Test Control 2',
        control_description='This is another test control',
        nist_mapping='NIST.800.171.3.1.2',
        review_frequency='Quarterly',
        last_review_date='2023-02-01',
        next_review_date='2023-05-01'
    )
    
    control_dict = control.to_dict()
    
    assert control_dict['control_id'] == 'TEST.1.002'
    assert control_dict['control_name'] == 'Test Control 2'
    assert control_dict['control_description'] == 'This is another test control'
    assert control_dict['nist_mapping'] == 'NIST.800.171.3.1.2'
    assert control_dict['review_frequency'] == 'Quarterly'
    assert control_dict['last_review_date'] == '2023-02-01'
    assert control_dict['next_review_date'] == '2023-05-01'

@pytest.mark.unit
@pytest.mark.models
@pytest.mark.parametrize(
    "frequency,expected_months",
    [
        ('Monthly', 1),
        ('Quarterly', 3),
        ('Semi-Annual', 6),
        ('Annual', 12),
        ('Biennial', 24),
        ('None', None),
        (None, None),
        ('Invalid', None)
    ]
)
def test_get_review_period_months(frequency, expected_months):
    """Test the get_review_period_months method."""
    control = Control(
        control_id='TEST.1.003',
        control_name='Test Control 3',
        review_frequency=frequency
    )
    
    assert control.get_review_period_months() == expected_months

@pytest.mark.unit
@pytest.mark.models
def test_calculate_next_review_date():
    """Test the calculate_next_review_date method."""
    # Test with Annual frequency
    control = Control(
        control_id='TEST.1.004',
        control_name='Test Control 4',
        review_frequency='Annual',
        last_review_date='2023-01-15'
    )
    
    next_date = control.calculate_next_review_date()
    assert next_date == '2024-01-15'
    
    # Test with Quarterly frequency
    control.review_frequency = 'Quarterly'
    next_date = control.calculate_next_review_date()
    assert next_date == '2023-04-15'
    
    # Test with no last review date
    control.last_review_date = None
    next_date = control.calculate_next_review_date()
    assert next_date is None
    
    # Test with no review frequency
    control.last_review_date = '2023-01-15'
    control.review_frequency = None
    next_date = control.calculate_next_review_date()
    assert next_date is None

@pytest.mark.unit
@pytest.mark.models
def test_is_review_due():
    """Test the is_review_due method."""
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    
    # Test with review date in the past
    control = Control(
        control_id='TEST.1.005',
        control_name='Test Control 5',
        next_review_date=yesterday
    )
    assert control.is_review_due() is True
    
    # Test with review date today
    control.next_review_date = today
    assert control.is_review_due() is True
    
    # Test with review date in the future
    control.next_review_date = tomorrow
    assert control.is_review_due() is False
    
    # Test with no review date
    control.next_review_date = None
    assert control.is_review_due() is False

@pytest.mark.unit
@pytest.mark.models
def test_get_by_id(app, init_database):
    """Test the get_by_id class method."""
    # Insert a test control
    execute_query(
        """
        INSERT INTO controls (
            controlid, controlname, controldescription, 
            nist_sp_800_171_mapping, policyreviewfrequency, 
            lastreviewdate, nextreviewdate
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (controlid) DO NOTHING
        """,
        (
            'TEST.1.006', 
            'Get By ID Test Control', 
            'This is a test control for get_by_id',
            'NIST.800.171.3.1.1',
            'Annual',
            '2023-01-01',
            '2024-01-01'
        ),
        commit=True
    )
    
    # Test get_by_id
    control = Control.get_by_id('TEST.1.006')
    assert control is not None
    assert control.control_id == 'TEST.1.006'
    assert control.control_name == 'Get By ID Test Control'
    assert control.control_description == 'This is a test control for get_by_id'
    assert control.nist_mapping == 'NIST.800.171.3.1.1'
    assert control.review_frequency == 'Annual'
    assert control.last_review_date == '2023-01-01'
    assert control.next_review_date == '2024-01-01'
    
    # Test with non-existent ID
    control = Control.get_by_id('NONEXISTENT')
    assert control is None
