"""Unit tests for the Evidence model."""

import pytest
import os
from datetime import date, timedelta
from cmmc_tracker.app.models.evidence import Evidence
from cmmc_tracker.app.services.database import execute_query

@pytest.mark.unit
@pytest.mark.models
def test_evidence_creation():
    """Test creating an Evidence object."""
    evidence = Evidence(
        evidence_id=1,
        control_id='TEST.1.001',
        title='Test Evidence',
        description='This is test evidence',
        file_path='/uploads/TEST.1.001/test_evidence.pdf',
        file_type='application/pdf',
        file_size=1024,
        uploaded_by='test_user',
        upload_date='2023-01-01',
        expiration_date='2024-01-01',
        status='Current'
    )

    assert evidence.evidence_id == 1
    assert evidence.control_id == 'TEST.1.001'
    assert evidence.title == 'Test Evidence'
    assert evidence.description == 'This is test evidence'
    assert evidence.file_path == '/uploads/TEST.1.001/test_evidence.pdf'
    assert evidence.file_type == 'application/pdf'
    assert evidence.file_size == 1024
    assert evidence.uploaded_by == 'test_user'
    assert evidence.upload_date == '2023-01-01'
    assert evidence.expiration_date == '2024-01-01'
    assert evidence.status == 'Current'

@pytest.mark.unit
@pytest.mark.models
def test_evidence_to_dict(app):
    """Test the to_dict method of the Evidence class."""
    evidence = Evidence(
        evidence_id=2,
        control_id='TEST.1.002',
        title='Test Evidence 2',
        description='This is another test evidence',
        file_path='/uploads/TEST.1.002/test_evidence2.pdf',
        file_type='application/pdf',
        file_size=2048,
        uploaded_by='test_user',
        upload_date='2023-02-01',
        expiration_date='2024-02-01',
        status='Current'
    )

    # Mock the control_name property to avoid database access
    evidence._control_name = 'Test Control'

    with app.app_context():
        evidence_dict = evidence.to_dict()

    assert evidence_dict['evidence_id'] == 2
    assert evidence_dict['control_id'] == 'TEST.1.002'
    assert evidence_dict['title'] == 'Test Evidence 2'
    assert evidence_dict['description'] == 'This is another test evidence'
    assert evidence_dict['file_path'] == '/uploads/TEST.1.002/test_evidence2.pdf'
    assert evidence_dict['file_type'] == 'application/pdf'
    assert evidence_dict['file_size'] == 2048
    assert evidence_dict['uploaded_by'] == 'test_user'
    assert evidence_dict['upload_date'] == '2023-02-01'
    assert evidence_dict['expiration_date'] == '2024-02-01'
    assert evidence_dict['status'] == 'Current'

@pytest.mark.unit
@pytest.mark.models
def test_evidence_filename():
    """Test the filename property."""
    evidence = Evidence(
        evidence_id=3,
        control_id='TEST.1.003',
        title='Test Evidence 3',
        file_path='/uploads/TEST.1.003/test_evidence3.pdf'
    )

    assert evidence.filename == 'test_evidence3.pdf'

    # Test with no file path
    evidence.file_path = None
    assert evidence.filename is None

    # Test with empty file path
    evidence.file_path = ''
    assert evidence.filename is None

@pytest.mark.unit
@pytest.mark.models
def test_evidence_file_extension():
    """Test the file_extension property."""
    evidence = Evidence(
        evidence_id=4,
        control_id='TEST.1.004',
        title='Test Evidence 4',
        file_path='/uploads/TEST.1.004/test_evidence4.pdf'
    )

    assert evidence.file_extension == '.pdf'

    # Test with no file path
    evidence.file_path = None
    assert evidence.file_extension is None

    # Test with empty file path
    evidence.file_path = ''
    assert evidence.file_extension is None

    # Test with file path having no extension
    evidence.file_path = '/uploads/TEST.1.004/test_evidence4'
    assert evidence.file_extension == ''

@pytest.mark.unit
@pytest.mark.models
def test_evidence_formatted_file_size():
    """Test the formatted_file_size property."""
    # Test with bytes
    evidence = Evidence(
        evidence_id=5,
        control_id='TEST.1.005',
        title='Test Evidence 5',
        file_size=500
    )
    assert evidence.formatted_file_size == '500 bytes'

    # Test with KB
    evidence.file_size = 1500
    assert evidence.formatted_file_size == '1.5 KB'

    # Test with MB
    evidence.file_size = 1500000
    assert evidence.formatted_file_size == '1.5 MB'

    # Test with GB
    evidence.file_size = 1500000000
    assert evidence.formatted_file_size == '1.5 GB'

    # Test with no file size
    evidence.file_size = None
    assert evidence.formatted_file_size == 'Unknown'

    # Test with zero file size
    evidence.file_size = 0
    assert evidence.formatted_file_size == '0 bytes'

@pytest.mark.unit
@pytest.mark.models
def test_evidence_is_expired():
    """Test the is_expired property."""
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Test with expiration date in the past
    evidence = Evidence(
        evidence_id=6,
        control_id='TEST.1.006',
        title='Test Evidence 6',
        expiration_date=yesterday
    )
    assert evidence.is_expired is True

    # Test with expiration date today
    evidence.expiration_date = today
    # The is_expired property should return False for today's date
    # This is because the implementation checks for expiration < today, not <=
    assert evidence.is_expired is False

    # Test with expiration date in the future
    evidence.expiration_date = tomorrow
    assert evidence.is_expired is False

    # Test with no expiration date
    evidence.expiration_date = None
    assert evidence.is_expired is False

@pytest.mark.unit
@pytest.mark.models
def test_get_by_id(app, init_database):
    """Test the get_by_id class method."""
    with app.app_context():
        # First, ensure we have a control to reference
        execute_query(
            """
            INSERT INTO controls (
                controlid, controlname
            ) VALUES (%s, %s)
            ON CONFLICT (controlid) DO NOTHING
            """,
            ('TEST.1.007', 'Evidence Test Control'),
            commit=True
        )

        # Insert a test evidence record
        execute_query(
            """
            INSERT INTO evidence (
                controlid, title, description, filepath, filetype, filesize,
                uploadedby, uploaddate, expirationdate, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                'TEST.1.007',
                'Get By ID Test Evidence',
                'This is a test evidence for get_by_id',
                '/uploads/TEST.1.007/test_evidence.pdf',
                'application/pdf',
                1024,
                'test_user',
                '2023-01-01',
                '2024-01-01',
                'Current'
            ),
            commit=True
        )

        # Get the evidence ID from the database
        evidence_data = execute_query(
            "SELECT evidenceid FROM evidence WHERE title = %s",
            ('Get By ID Test Evidence',),
            fetch_one=True
        )
        evidence_id = evidence_data['evidenceid']

        # Test get_by_id
        evidence = Evidence.get_by_id(evidence_id)
        assert evidence is not None
        assert evidence.evidence_id == evidence_id
        assert evidence.control_id == 'TEST.1.007'
        assert evidence.title == 'Get By ID Test Evidence'
        assert evidence.description == 'This is a test evidence for get_by_id'
        assert evidence.file_path == '/uploads/TEST.1.007/test_evidence.pdf'
        assert evidence.file_type == 'application/pdf'
        assert evidence.file_size == 1024
        assert evidence.uploaded_by == 'test_user'
        assert evidence.upload_date == '2023-01-01'
        assert evidence.expiration_date == '2024-01-01'
        assert evidence.status == 'Current'

        # Test with non-existent ID
        evidence = Evidence.get_by_id(9999)
        assert evidence is None
