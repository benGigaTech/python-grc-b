"""Unit tests for the MFA service."""

import pytest
import re
import pyotp
from cmmc_tracker.app.services.mfa import (
    generate_totp_secret,
    get_totp_uri,
    generate_qr_code,
    verify_totp
)

@pytest.mark.unit
@pytest.mark.services
def test_generate_totp_secret():
    """Test the generate_totp_secret function."""
    # Generate a secret
    secret = generate_totp_secret()
    
    # Secret should be a non-empty string
    assert secret is not None
    assert isinstance(secret, str)
    assert len(secret) > 0
    
    # Secret should be a valid base32 string
    assert re.match(r'^[A-Z2-7]+=*$', secret) is not None
    
    # Generate another secret and ensure they're different
    another_secret = generate_totp_secret()
    assert secret != another_secret

@pytest.mark.unit
@pytest.mark.services
def test_get_totp_uri():
    """Test the get_totp_uri function."""
    # Generate a URI
    username = 'test_user'
    secret = generate_totp_secret()
    uri = get_totp_uri(username, secret)
    
    # URI should be a non-empty string
    assert uri is not None
    assert isinstance(uri, str)
    assert len(uri) > 0
    
    # URI should have the correct format
    assert uri.startswith('otpauth://totp/')
    assert username in uri
    assert secret in uri
    assert 'issuer=CMMC%20Tracker' in uri
    
    # Test with custom issuer
    custom_issuer = 'Custom Issuer'
    uri = get_totp_uri(username, secret, issuer=custom_issuer)
    assert f'issuer={custom_issuer.replace(" ", "%20")}' in uri

@pytest.mark.unit
@pytest.mark.services
def test_generate_qr_code():
    """Test the generate_qr_code function."""
    # Generate a QR code
    username = 'test_user'
    secret = generate_totp_secret()
    uri = get_totp_uri(username, secret)
    qr_code = generate_qr_code(uri)
    
    # QR code should be a non-empty string
    assert qr_code is not None
    assert isinstance(qr_code, str)
    assert len(qr_code) > 0
    
    # QR code should be a data URL
    assert qr_code.startswith('data:image/png;base64,')
    
    # Test with invalid URI
    qr_code = generate_qr_code(None)
    assert qr_code is None
    
    qr_code = generate_qr_code('')
    assert qr_code is None

@pytest.mark.unit
@pytest.mark.services
def test_verify_totp():
    """Test the verify_totp function."""
    # Generate a secret
    secret = generate_totp_secret()
    
    # Generate a valid token
    totp = pyotp.TOTP(secret)
    valid_token = totp.now()
    
    # Test with valid token
    assert verify_totp(secret, valid_token) is True
    
    # Test with invalid token
    assert verify_totp(secret, '000000') is False
    
    # Test with None secret
    assert verify_totp(None, valid_token) is False
    
    # Test with empty secret
    assert verify_totp('', valid_token) is False
    
    # Test with None token
    assert verify_totp(secret, None) is False
    
    # Test with empty token
    assert verify_totp(secret, '') is False
