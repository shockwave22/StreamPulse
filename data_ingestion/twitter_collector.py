import tweepy
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from config import Config
from database.models import Tweet, NetflixTitle
from database.database import db_manager
from retry import retry

logger = logging.getLogger(__name__)

class TwitterCollector:
    def __init__(self):
        self.api = self._setup_twitter_api()
    
    def _setup_twitter_api(self):
        """Initialize Twitter API client"""
        try:
            client = tweepy.Client(
                bearer_token=Config.TWITTER_BEARER_TOKEN,
                consumer_key=Config.TWITTER_API_KEY,
                consumer_secret=Config.TWITTER_API_SECRET,
                access_token=Config.TWITTER_ACCESS_TOKEN,
                access_token_secret=Config.TWITTER_ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=True
            )
            logger.info("Twitter API client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Twitter API: {e}")
            raise
    
    @retry(tries=3, delay=5, backoff=2)
    def collect_tweets_for_title(self, title: str, max_results: int = 100) -> List[Dict]:
        """Collect tweets for a specific Netflix title"""
        try:
            # Construct search query
            query = f'"{title}" OR #{title.replace(" ", "")} -is:retweet lang:en'
            
            # Search for tweets
            tweets = tweepy.Paginator(
                self.api.search_recent_tweets,
                query=query,
                max_results=min(max_results, 100),
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'context_annotations']
            ).flatten(limit=max_results)
            
            tweet_data = []
            for tweet in tweets:
                tweet_data.append({
                    'tweet_id': tweet.id,
                    'text': tweet.text,
                    'author_id': tweet.author_id,
                    'created_at': tweet.created_at,
                    'retweet_count': tweet.public_metrics.get('retweet_count', 0),
                    'like_count': tweet.public_metrics.get('like_count', 0),
                    'reply_count': tweet.public_metrics.get('reply_count', 0)
                })
            
            logger.info(f"Collected {len(tweet_data)} tweets for '{title}'")
            return tweet_data
            
        except Exception as e:
            logger.error(f"Error collecting tweets for '{title}': {e}")
            return []
    
    def store_tweets(self, title: str, tweet_data: List[Dict]):
        """Store collected tweets in database"""
        session = db_manager.get_session()
        try:
            # Get or create Netflix title
            netflix_title = session.query(NetflixTitle).filter_by(title=title).first()
            if not netflix_title:
                netflix_title = NetflixTitle(title=title)
                session.add(netflix_title)
                session.commit()
            
            # Store tweets
            stored_count = 0
            for tweet_info in tweet_data:
                # Check if tweet already exists
                existing_tweet = session.query(Tweet).filter_by(
                    tweet_id=str(tweet_info['tweet_id'])
                ).first()
                
                if not existing_tweet:
                    tweet = Tweet(
                        tweet_id=str(tweet_info['tweet_id']),
                        title_id=netflix_title.id,
                        text=tweet_info['text'],
                        author=str(tweet_info['author_id']),
                        created_at=tweet_info['created_at'],
                        retweet_count=tweet_info['retweet_count'],
                        like_count=tweet_info['like_count'],
                        reply_count=tweet_info['reply_count']
                    )
                    session.add(tweet)
                    stored_count += 1
            
            session.commit()
            logger.info(f"Stored {stored_count} new tweets for '{title}'")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing tweets for '{title}': {e}")
        finally:
            session.close()
    
    def collect_all_titles(self):
        """Collect tweets for all Netflix titles"""
        for title in Config.NETFLIX_TITLES:
            try:
                tweet_data = self.collect_tweets_for_title(title, Config.TWEETS_PER_TITLE)
                self.store_tweets(title, tweet_data)
            except Exception as e:
                logger.error(f"Failed to collect tweets for '{title}': {e}")
                continue