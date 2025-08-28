from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
import sys
import os

# Add project root to Python path
sys.path.append('/opt/airflow/dags/streampulse')

from data_ingestion.twitter_collector import TwitterCollector
from data_ingestion.reddit_collector import RedditCollector
from data_ingestion.survey_collector import SurveyCollector
from sentiment_analysis.analyzer import SentimentAnalyzer
from data_aggregation.aggregator import DataAggregator
import logging

logger = logging.getLogger(__name__)

# Default arguments for the DAG
default_args = {
    'owner': 'streampulse',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

# Create the DAG
dag = DAG(
    'streampulse_pipeline',
    default_args=default_args,
    description='StreamPulse data collection and processing pipeline',
    schedule_interval=timedelta(hours=6),  # Run every 6 hours
    max_active_runs=1,
    tags=['streampulse', 'sentiment-analysis', 'netflix']
)

# Task functions
def collect_twitter_data(**context):
    """Collect Twitter data for all Netflix titles"""
    try:
        collector = TwitterCollector()
        collector.collect_all_titles()
        logger.info("Twitter data collection completed successfully")
    except Exception as e:
        logger.error(f"Twitter data collection failed: {e}")
        raise

def collect_reddit_data(**context):
    """Collect Reddit data for all Netflix titles"""
    try:
        collector = RedditCollector()
        collector.collect_all_titles()
        logger.info("Reddit data collection completed successfully")
    except Exception as e:
        logger.error(f"Reddit data collection failed: {e}")
        raise

def collect_survey_data(**context):
    """Generate/collect survey data"""
    try:
        collector = SurveyCollector()
        # For demo purposes, we generate mock data
        # In production, this would load real survey data
        collector.generate_all_mock_data()
        logger.info("Survey data collection completed successfully")
    except Exception as e:
        logger.error(f"Survey data collection failed: {e}")
        raise

def process_sentiment_analysis(**context):
    """Process sentiment analysis for all new content"""
    try:
        analyzer = SentimentAnalyzer()
        analyzer.process_all_pending()
        logger.info("Sentiment analysis completed successfully")
    except Exception