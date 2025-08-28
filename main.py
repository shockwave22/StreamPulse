#!/usr/bin/env python3
"""
StreamPulse Main Application Entry Point
"""
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from database.database import db_manager
from data_ingestion.twitter_collector import TwitterCollector
from data_ingestion.reddit_collector import RedditCollector
from data_ingestion.survey_collector import SurveyCollector
from sentiment_analysis.analyzer import SentimentAnalyzer
from data_aggregation.aggregator import DataAggregator

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def setup_database():
    """Initialize database and create tables"""
    logger.info("Setting up database...")
    db_manager._create_tables()
    logger.info("Database setup completed")

def collect_initial_data():
    """Collect initial data for all Netflix titles"""
    logger.info("Starting initial data collection...")
    
    # Initialize collectors
    survey_collector = SurveyCollector()
    twitter_collector = TwitterCollector()
    reddit_collector = RedditCollector()
    
    # Generate mock survey data first
    logger.info("Generating mock survey data...")
    survey_collector.generate_all_mock_data()
    
    # Collect social media data
    logger.info("Collecting Twitter data...")
    twitter_collector.collect_all_titles()
    
    logger.info("Collecting Reddit data...")
    reddit_collector.collect_all_titles()
    
    logger.info("Initial data collection completed")

def process_sentiment():
    """Process sentiment analysis for all collected data"""
    logger.info("Starting sentiment analysis...")
    analyzer = SentimentAnalyzer()
    analyzer.process_all_pending()
    logger.info("Sentiment analysis completed")

def aggregate_data():
    """Aggregate data for dashboard"""
    logger.info("Starting data aggregation...")
    aggregator = DataAggregator()
    aggregator.aggregate_weekly_data()
    logger.info("Data aggregation completed")

def run_full_pipeline():
    """Run the complete data pipeline"""
    setup_database()
    collect_initial_data()
    process_sentiment()
    aggregate_data()
    logger.info("Full pipeline completed successfully!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="StreamPulse Data Pipeline")
    parser.add_argument('--setup', action='store_true', help='Setup database')
    parser.add_argument('--collect', action='store_true', help='Collect data')
    parser.add_argument('--sentiment', action='store_true', help='Process sentiment')
    parser.add_argument('--aggregate', action='store_true', help='Aggregate data')
    parser.add_argument('--full', action='store_true', help='Run full pipeline')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_database()
    elif args.collect:
        collect_initial_data()
    elif args.sentiment:
        process_sentiment()
    elif args.aggregate:
        aggregate_data()
    elif args.full:
        run_full_pipeline()
    else:
        print("Usage: python main.py [--setup|--collect|--sentiment|--aggregate|--full]")