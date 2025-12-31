import random
import requests
import re
import base64
from config import FAST2SMS_API_KEY
from typing import Dict, Optional
from utils.email import send_email
from utils.email_templates import EMAIL_VERIFICATION_TEMPLATE
import time

# In-memory OTP storage (use Redis in production)
# Store as {identifier: {otp: str, type: str, timestamp: float}}
mobile_otp_storage: Dict[str, Dict[str, str]] = {}
email_otp_storage: Dict[str, Dict[str, str]] = {}

# OTP expiration time in seconds (10 minutes)
OTP_EXPIRATION_TIME = 600

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def generate_static_mobile_otp() -> str:
    """
    Generate a static OTP for mobile verification.
    NOTE: This is for TESTING PURPOSES ONLY and should not be used in production.
    """
    return "999999"  # Static OTP for testing

def is_valid_email(email: str) -> bool:
    """Check if the provided string is a valid email address."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_otp_expired(timestamp: float) -> bool:
    """Check if an OTP has expired."""
    return time.time() - timestamp > OTP_EXPIRATION_TIME

def cleanup_expired_otps() -> None:
    """Remove expired OTPs from storage."""
    current_time = time.time()
    
    # Clean up expired mobile OTPs
    expired_mobile_otps = [
        identifier for identifier, data in mobile_otp_storage.items()
        if current_time - float(data.get("timestamp", 0)) > OTP_EXPIRATION_TIME
    ]
    for identifier in expired_mobile_otps:
        del mobile_otp_storage[identifier]
    
    # Clean up expired email OTPs
    expired_email_otps = [
        identifier for identifier, data in email_otp_storage.items()
        if current_time - float(data.get("timestamp", 0)) > OTP_EXPIRATION_TIME
    ]
    for identifier in expired_email_otps:
        del email_otp_storage[identifier]

def store_mobile_otp(mobile_number: str, otp: str) -> None:
    """Store OTP for a mobile number."""
    mobile_otp_storage[mobile_number] = {
        "otp": otp,
        "type": "mobile",
        "timestamp": str(time.time())
    }

def store_email_otp(email: str, otp: str) -> None:
    """Store OTP for an email address."""
    email_otp_storage[email] = {
        "otp": otp,
        "type": "email",
        "timestamp": str(time.time())
    }

def get_mobile_otp(mobile_number: str) -> Optional[Dict[str, str]]:
    """Retrieve OTP data for a mobile number."""
    data = mobile_otp_storage.get(mobile_number)
    if data and is_otp_expired(float(data.get("timestamp", 0))):
        del mobile_otp_storage[mobile_number]
        return None
    return data

def get_email_otp(email: str) -> Optional[Dict[str, str]]:
    """Retrieve OTP data for an email address."""
    data = email_otp_storage.get(email)
    if data and is_otp_expired(float(data.get("timestamp", 0))):
        del email_otp_storage[email]
        return None
    return data

async def send_otp(identifier: str) -> bool:
    """
    Send OTP to either mobile number or email address.
    
    Args:
        identifier (str): Either a mobile number or email address
        
    Returns:
        bool: True if OTP was sent successfully, False otherwise
    """
    # Clean up expired OTPs before sending new ones
    cleanup_expired_otps()
    
    # Check if identifier is an email
    if is_valid_email(identifier):
        # Generate random OTP for email
        otp = generate_otp()
        # Store OTP with type info
        store_email_otp(identifier, otp)
        
        # Send email with OTP using the template
        html_content = EMAIL_VERIFICATION_TEMPLATE.replace("{{otp_code}}", otp).replace("{{CURRENT_YEAR}}", str(time.localtime().tm_year))
        subject = "Email Verification OTP"
        return send_email(identifier, subject, html_content)
    else:
        # Generate static OTP for mobile (TESTING PURPOSES ONLY)
        otp = generate_static_mobile_otp()
        # Store OTP with type info
        store_mobile_otp(identifier, otp)
        
        # For mobile, we'll use the existing logic (hardcoded for now)
        # In production, this would send an SMS
        return True

async def send_email_otp(email: str) -> bool:
    """
    Send OTP specifically for email verification.
    
    Args:
        email (str): Email address to send OTP to
        
    Returns:
        bool: True if OTP was sent successfully, False otherwise
    """
    # Validate email format
    if not is_valid_email(email):
        return False
    
    # Clean up expired OTPs
    cleanup_expired_otps()
    
    # Generate and store OTP
    otp = generate_otp()
    store_email_otp(email, otp)
    
    # Send email with OTP using the template
    html_content = EMAIL_VERIFICATION_TEMPLATE.replace("{{otp_code}}", otp).replace("{{CURRENT_YEAR}}", str(time.localtime().tm_year))
    subject = "Email Verification OTP"
    return send_email(email, subject, html_content)

def verify_mobile_otp(mobile_number: str, otp: str) -> bool:
    """
    Verify OTP for a mobile number.
    
    Args:
        mobile_number (str): Mobile number to verify
        otp (str): The OTP to verify (plain text only)
        
    Returns:
        bool: True if OTP is valid, False otherwise
    """
    # For mobile OTPs, we only accept plain text OTPs
    stored_data = get_mobile_otp(mobile_number)
    if stored_data and stored_data["otp"] == otp:
        del mobile_otp_storage[mobile_number]
        return True
    return False

def verify_email_otp(email: str, otp: str) -> bool:
    """
    Verify OTP for an email address.
    
    Args:
        email (str): Email address to verify
        otp (str): The OTP to verify (can be base64 encoded)
        
    Returns:
        bool: True if OTP is valid, False otherwise
    """
    # Try to decode OTP if it's base64 encoded
    try:
        decoded_otp = base64.b64decode(otp).decode('utf-8')
        # If decoding succeeds, use the decoded OTP
        otp_to_verify = decoded_otp
    except Exception:
        # If decoding fails, assume it's not base64 encoded
        otp_to_verify = otp
    
    stored_data = get_email_otp(email)
    if stored_data and stored_data["otp"] == otp_to_verify:
        del email_otp_storage[email]
        return True
    return False

def verify_otp(identifier: str, otp: str) -> bool:
    """
    Verify OTP for either mobile number or email address.
    
    Args:
        identifier (str): Either a mobile number or email address
        otp (str): The OTP to verify
        
    Returns:
        bool: True if OTP is valid, False otherwise
    """
    # Check if identifier is an email
    if is_valid_email(identifier):
        return verify_email_otp(identifier, otp)
    else:
        return verify_mobile_otp(identifier, otp)

def get_email_by_otp(otp: str) -> Optional[str]:
    """
    Find the email associated with an OTP (for backward compatibility).
    
    Args:
        otp (str): The OTP to search for
        
    Returns:
        Optional[str]: The email address if found, None otherwise
    """
    # Clean up expired OTPs first
    cleanup_expired_otps()
    
    # Search through email OTP storage
    for email, data in email_otp_storage.items():
        if data.get("otp") == otp:
            return email
    return None
