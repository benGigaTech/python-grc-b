"""MFA service for the CMMC Tracker application."""

import logging
import io
import base64
import pyotp
import qrcode
from flask import current_app

logger = logging.getLogger(__name__)

def generate_totp_secret():
    """
    Generate a new TOTP secret key.
    
    Returns:
        str: The generated secret key
    """
    return pyotp.random_base32()

def get_totp_uri(username, secret, issuer="CMMC Tracker"):
    """
    Generate a TOTP URI for the user.
    
    Args:
        username: The username
        secret: The TOTP secret key
        issuer: The issuer name for the TOTP
        
    Returns:
        str: The TOTP URI for use with authenticator apps
    """
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name=issuer
    )

def generate_qr_code(totp_uri):
    """
    Generate a QR code image for the TOTP URI.
    
    Args:
        totp_uri: The TOTP URI
        
    Returns:
        str: Base64 encoded QR code image data
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        return None

def verify_totp(secret, token):
    """
    Verify a TOTP token against the secret.
    
    Args:
        secret: The TOTP secret key
        token: The TOTP token to verify
        
    Returns:
        bool: True if the token is valid, False otherwise
    """
    if not secret or not token:
        return False
        
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(token)
    except Exception as e:
        logger.error(f"Error verifying TOTP token: {e}")
        return False 