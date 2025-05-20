import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key")
    FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
