import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///streampulse.db')
    
    # API Keys
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'StreamPulse:v1.0')
    
    # Netflix titles to track
    NETFLIX_TITLES = [
        'Stranger Things',
        'The Witcher',
        'Wednesday',
        'Ozark',
        'The Crown',
        'Bridgerton',
        'Squid Game',
        'Money Heist',
        'Dark',
        'The Umbrella Academy'
    ]
    
    # Data collection settings
    TWEETS_PER_TITLE = 100
    REDDIT_COMMENTS_LIMIT = 50
    DATA_COLLECTION_INTERVAL_HOURS = 6
    
    # Sentiment analysis settings
    SENTIMENT_MODEL = 'vader'  # 'vader' or 'transformers'
    TRANSFORMER_MODEL = 'distilbert-base-uncased-finetuned-sst-2-english'
    
    # Dashboard settings
    STREAMLIT_PORT = 8501
    DASHBOARD_REFRESH_INTERVAL = 300  # seconds
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/streampulse.log'
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent
    DATA_DIR = PROJECT_ROOT / 'data'
    LOGS_DIR = PROJECT_ROOT / 'logs'
    
    # Ensure directories exist
    DATA_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)