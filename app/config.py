import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
SENDER_EMAIL = os.getenv("GMAIL_ADDRESS")
PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
AWS_REGION = os.getenv("AWS_REGION")
IMAGES_BUCKET_NAME = os.getenv("IMAGES_BUCKET_NAME")
JWT_SECRET = os.getenv("JWT_SECRET")
FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 6 * 30 * 24 * 60  # 6 months
MAX_DISTANCE_KM = 15
# ✅ Replace with your desired dev-only credentials
DOCS_USERNAME = "admin"
DOCS_PASSWORD = "secret123"