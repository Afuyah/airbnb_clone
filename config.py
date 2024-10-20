import os

class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_default_secret_key'

    # Database configuration using PostgreSQL
    SQLALCHEMY_DATABASE_URI = 'sqlite:///houser.db' # 'postgresql://postgres:FogLdsGbyuRXtlcMXoErOCssOoEyiNTh@autorack.proxy.rlwy.net:52876/railway'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # M-Pesa Configuration
    MPESA_BASE_URL = os.environ.get('MPESA_BASE_URL') or 'https://sandbox.safaricom.co.ke'
    MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE') or 'your_shortcode'
    MPESA_LIPA_NA_MPESA_URL = os.path.join(MPESA_BASE_URL, 'mpesa/stkpush/v1/processrequest')
    MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY') or 'your_consumer_key'
    MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET') or 'your_consumer_secret'
    MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY') or 'your_passkey'
    MPESA_LIVE_URL = os.environ.get('MPESA_LIVE_URL') or 'https://api.safaricom.co.ke'

    # Logging Configuration
    LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', 'INFO').upper()
    LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOGGING_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.log')

    # Payment callback URL
    PAYMENT_CALLBACK_URL = os.environ.get('PAYMENT_CALLBACK_URL') or 'http://yourdomain.com/payment/callback'

    # Email Configuration (Optional)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.example.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true') == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your_email@example.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'your_email_password'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@example.com'


