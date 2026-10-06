import os

class Config:
    """Application configuration with deliberate missing environment handling."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "demo-secret")
    DEBUG = False
    
    # Bug: DATABASE_URL is required directly from environ without fallback or proper validation
    # If not set in environment, this is None, causing initialization error in database.py
    DATABASE_URL = os.environ.get("DATABASE_URL")
