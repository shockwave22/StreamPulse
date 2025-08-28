import logging
from typing import Dict, List, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline
from database.models import Tweet, RedditComment, SentimentScore
from database.database import db_manager
from config import Config

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self, model_type: str = None):
        self.model_type = model_type or Config.SENTIMENT_MODEL
        self.vader_analyzer = SentimentIntensityAnalyzer()
        self.transformer_pipeline = None
        
        if self.model_type == 'transformers':
            self._load_transformer_model()
    
    def _load_transformer_model(self):
        """Load transformer model for sentiment analysis"""
        try:
            self.transformer_pipeline = pipeline(
                "sentiment-analysis",
                model=Config.TRANSFORMER_MODEL,
                return_all_scores=True
            )
            logger.info(f"Transformer model loaded: {Config.TRANSFORMER_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load transformer model: {e}")
            self.model_type = 'vader'  # Fallback to VADER
    
    def analyze_text_vader(self, text: str) -> Dict:
        """Analyze sentiment using VADER"""
        scores = self.vader_analyzer.polarity_scores(text)
        
        # Determine sentiment class
        if scores['compound'] >= 0.05:
            sentiment_class = 'positive'
        elif scores['compound'] <= -0.05:
            sentiment_class = 'negative'
        else:
            sentiment_class = 'neutral'
        
        return {
            'polarity_score': scores['compound'],
            'sentiment_class': sentiment_class,
            'confidence_score': max(scores['pos'], scores['neu'], scores['neg']),
            'model_used': 'vader'
        }
    
    def analyze_text_transformer(self, text: str) -> Dict:
        """Analyze sentiment using transformer model"""
        if not self.transformer_pipeline:
            return self.analyze_text_vader(text)
        
        try:
            results = self.transformer_pipeline(text[:512])  # Truncate to model limit
            
            # Get the highest scoring sentiment
            best_result = max(results[0], key=lambda x: x['score'])
            
            # Map labels to our format
            label_mapping = {
                'POSITIVE': 'positive',
                'NEGATIVE': 'negative',
                'NEUTRAL': 'neutral'
            }
            
            sentiment_class = label_mapping.get(best_result['label'].upper(), 'neutral')
            
            # Convert to polarity score (-1 to 1)
            if sentiment_class == 'positive':
                polarity_score = best_result['score']
            elif sentiment_class == 'negative':
                polarity_score = -best_result['score']
            else:
                polarity_score = 0.0
            
            return {
                'polarity_score': polarity_score,
                'sentiment_class': sentiment_class,
                'confidence_score': best_result['score'],
                'model_used': 'transformers'
            }
            
        except Exception as e:
            logger.error(f"Transformer analysis failed: {e}")
            return self.analyze_text_vader(text)
    
    def analyze_text(self, text: str) -> Dict:
        """Analyze sentiment using the configured model"""
        if self.model_type == 'transformers':
            return self.analyze_text_transformer(text)
        else:
            return self.analyze_text_vader(text)
    
    def process_tweets(self, limit: Optional[int] = None):
        """Process sentiment for tweets without sentiment scores"""
        session = db_manager.get_session()
        try:
            # Get tweets without sentiment scores
            query = session.query(Tweet).filter(
                ~Tweet.sentiment_scores.any()
            )
            
            if limit:
                query = query.limit(limit)
            
            tweets = query.all()
            processed_count = 0
            
            for tweet in tweets:
                try:
                    # Analyze sentiment
                    sentiment_result = self.analyze_text(tweet.text)
                    
                    # Store sentiment score
                    sentiment_score = SentimentScore(
                        tweet_id=tweet.id,
                        polarity_score=sentiment_result['polarity_score'],
                        sentiment_class=sentiment_result['sentiment_class'],
                        confidence_score=sentiment_result['confidence_score'],
                        model_used=sentiment_result['model_used']
                    )
                    
                    session.add(sentiment_score)
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing tweet {tweet.id}: {e}")
                    continue
            
            session.commit()
            logger.info(f"Processed sentiment for {processed_count} tweets")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error processing tweets: {e}")
        finally:
            session.close()
    
    def process_reddit_comments(self, limit: Optional[int] = None):
        """Process sentiment for Reddit comments without sentiment scores"""
        session = db_manager.get_session()
        try:
            # Get comments without sentiment scores
            query = session.query(RedditComment).filter(
                ~RedditComment.sentiment_scores.any()
            )
            
            if limit:
                query = query.limit(limit)
            
            comments = query.all()
            processed_count = 0
            
            for comment in comments:
                try:
                    # Analyze sentiment
                    sentiment_result = self.analyze_text(comment.text)
                    
                    # Store sentiment score
                    sentiment_score = SentimentScore(
                        reddit_comment_id=comment.id,
                        polarity_score=sentiment_result['polarity_score'],
                        sentiment_class=sentiment_result['sentiment_class'],
                        confidence_score=sentiment_result['confidence_score'],
                        model_used=sentiment_result['model_used']
                    )
                    
                    session.add(sentiment_score)
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing comment {comment.id}: {e}")
                    continue
            
            session.commit()
            logger.info(f"Processed sentiment for {processed_count} comments")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error processing comments: {e}")
        finally:
            session.close()
    
    def process_all_pending(self):
        """Process sentiment for all pending tweets and comments"""
        logger.info("Starting sentiment analysis for all pending items")
        self.process_tweets()
        self.process_reddit_comments()
        logger.info("Sentiment analysis completed")