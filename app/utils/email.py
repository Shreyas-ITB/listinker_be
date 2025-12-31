import smtplib
import ssl
from email.mime.text import MIMEText
from config import SENDER_EMAIL as sender_email
from config import PASSWORD as password
from email.mime.multipart import MIMEMultipart
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(recipient: str, subject: str, html_content: str) -> bool:
    """
    Send an email using Gmail SMTP.
    
    Args:
        recipient (str): Recipient email address
        subject (str): Email subject
        html_content (str): HTML content of the email
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get credentials from environment variables
        
        
        if not sender_email or not password:
            logger.error("GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set in environment variables")
            return False
            
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = recipient
        
        # Create HTML part
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Create secure connection and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient, message.as_string())
            
        logger.info(f"Email sent successfully to {recipient}")
        return True
        
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {e}")
        return False
    except Exception as e:
        logger.error(f"An error occurred while sending email: {e}")
        return False
