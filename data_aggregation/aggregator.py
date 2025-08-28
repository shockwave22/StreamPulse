import logging
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import func, and_
from database.models import (
    NetflixTitle, Tweet, RedditComment, SurveyResponse, 
    SentimentScore, AggregatedMetrics
)
from database.database import db_manager

logger = logging.getLogger(__name__)

class DataAggregator:
    def __init__(self):
        pass
    
    def aggregate_daily_sentiment(self, date: datetime = None):
        """Aggregate sentiment data for a specific date"""
        if date is None:
            date = datetime.now().date()
        
        session = db_manager.get_session()
        try:
            # Get all Netflix titles
            titles = session.query(NetflixTitle).all()
            
            for title in titles:
                # Aggregate Twitter sentiment
                self._aggregate_twitter_sentiment(session, title, date)
                
                # Aggregate Reddit sentiment
                self._aggregate_reddit_sentiment(session, title, date)
                
                # Aggregate survey data
                self._aggregate_survey_data(session, title, date)
            
            session.commit()
            logger.info(f"Daily aggregation completed for {date}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error in daily aggregation: {e}")
        finally:
            session.close()
    
    def _aggregate_twitter_sentiment(self, session, title: NetflixTitle, date: datetime):
        """Aggregate Twitter sentiment for a title and date"""
        start_date = datetime.combine(date, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        
        # Query sentiment scores for tweets
        sentiment_query = session.query(
            func.avg(SentimentScore.polarity_score).label('avg_sentiment'),
            func.count(SentimentScore.sentiment_class).label('total_count'),
            SentimentScore.sentiment_class
        ).join(Tweet).filter(
            and_(
                Tweet.title_id == title.id,
                Tweet.created_at >= start_date,
                Tweet.created_at < end_date
            )
        ).group_by(SentimentScore.sentiment_class)
        
        results = sentiment_query.all()
        
        if results:
            # Calculate aggregated metrics
            sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
            total_sentiment = 0
            total_count = 0
            
            for result in results:
                sentiment_counts[result.sentiment_class] = result.total_count
                total_sentiment += result.avg_sentiment * result.total_count
                total_count += result.total_count
            
            avg_sentiment = total_sentiment / total_count if total_count > 0 else 0
            
            # Store or update aggregated metrics
            self._store_aggregated_metrics(
                session, title.id, 'twitter', date,
                avg_sentiment, sentiment_counts, total_count
            )
    
    def _aggregate_reddit_sentiment(self, session, title: NetflixTitle, date: datetime):
        """Aggregate Reddit sentiment for a title and date"""
        start_date = datetime.combine(date, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        
        # Query sentiment scores for comments
        sentiment_query = session.query(
            func.avg(SentimentScore.polarity_score).label('avg_sentiment'),
            func.count(SentimentScore.sentiment_class).label('total_count'),
            SentimentScore.sentiment_class
        ).join(RedditComment).filter(
            and_(
                RedditComment.title_id == title.id,
                RedditComment.created_at >= start_date,
                RedditComment.created_at < end_date
            )
        ).group_by(SentimentScore.sentiment_class)
        
        results = sentiment_query.all()
        
        if results:
            # Calculate aggregated metrics
            sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
            total_sentiment = 0
            total_count = 0
            
            for result in results:
                sentiment_counts[result.sentiment_class] = result.total_count
                total_sentiment += result.avg_sentiment * result.total_count
                total_count += result.total_count
            
            avg_sentiment = total_sentiment / total_count if total_count > 0 else 0
            
            # Store or update aggregated metrics
            self._store_aggregated_metrics(
                session, title.id, 'reddit', date,
                avg_sentiment, sentiment_counts, total_count
            )
    
    def _aggregate_survey_data(self, session, title: NetflixTitle, date: datetime):
        """Aggregate survey data for a title and date"""
        start_date = datetime.combine(date, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        
        # Query survey responses
        survey_query = session.query(
            func.avg(SurveyResponse.satisfaction_score).label('avg_satisfaction'),
            func.avg(SurveyResponse.completion_rate).label('avg_completion'),
            func.avg(SurveyResponse.would_recommend.cast('integer')).label('recommendation_rate'),
            func.count(SurveyResponse.id).label('total_count')
        ).filter(
            and_(
                SurveyResponse.title_id == title.id,
                SurveyResponse.created_at >= start_date,
                SurveyResponse.created_at < end_date
            )
        )
        
        result = survey_query.first()
        
        if result and result.total_count > 0:
            # Store survey aggregated metrics
            existing_metric = session.query(AggregatedMetrics).filter_by(
                title_id=title.id,
                platform='survey',
                date=start_date
            ).first()
            
            if existing_metric:
                existing_metric.avg_satisfaction = result.avg_satisfaction
                existing_metric.avg_completion_rate = result.avg_completion
                existing_metric.recommendation_rate = result.recommendation_rate
                existing_metric.total_count = result.total_count
            else:
                metric = AggregatedMetrics(
                    title_id=title.id,
                    platform='survey',
                    date=start_date,
                    avg_satisfaction=result.avg_satisfaction,
                    avg_completion_rate=result.avg_completion,
                    recommendation_rate=result.recommendation_rate,
                    total_count=result.total_count
                )
                session.add(metric)
    
    def _store_aggregated_metrics(self, session, title_id: int, platform: str, 
                                date: datetime, avg_sentiment: float, 
                                sentiment_counts: Dict, total_count: int):
        """Store or update aggregated metrics"""
        start_date = datetime.combine(date, datetime.min.time())
        
        existing_metric = session.query(AggregatedMetrics).filter_by(
            title_id=title_id,
            platform=platform,
            date=start_date
        ).first()
        
        if existing_metric:
            existing_metric.avg_sentiment = avg_sentiment
            existing_metric.positive_count = sentiment_counts['positive']
            existing_metric.neutral_count = sentiment_counts['neutral']
            existing_metric.negative_count = sentiment_counts['negative']
            existing_metric.total_count = total_count
        else:
            metric = AggregatedMetrics(
                title_id=title_id,
                platform=platform,
                date=start_date,
                avg_sentiment=avg_sentiment,
                positive_count=sentiment_counts['positive'],
                neutral_count=sentiment_counts['neutral'],
                negative_count=sentiment_counts['negative'],
                total_count=total_count
            )
            session.add(metric)
    
    def aggregate_weekly_data(self):
        """Aggregate data for the past week"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        current_date = start_date
        while current_date <= end_date:
            self.aggregate_daily_sentiment(current_date)
            current_date += timedelta(days=1)
        
        logger.info(f"Weekly aggregation completed from {start_date} to {end_date}")
    
    def get_title_summary(self, title_id: int, days: int = 7) -> Dict:
        """Get summary metrics for a title over the past N days"""
        session = db_manager.get_session()
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Query aggregated metrics
            metrics = session.query(AggregatedMetrics).filter(
                and_(
                    AggregatedMetrics.title_id == title_id,
                    AggregatedMetrics.date >= start_date,
                    AggregatedMetrics.date <= end_date
                )
            ).all()
            
            summary = {
                'twitter': {'avg_sentiment': 0, 'total_count': 0, 'sentiment_breakdown': {}},
                'reddit': {'avg_sentiment': 0, 'total_count': 0, 'sentiment_breakdown': {}},
                'survey': {'avg_satisfaction': 0, 'recommendation_rate': 0, 'total_count': 0}
            }
            
            for metric in metrics:
                if metric.platform in ['twitter', 'reddit']:
                    summary[metric.platform]['avg_sentiment'] += metric.avg_sentiment or 0
                    summary[metric.platform]['total_count'] += metric.total_count or 0
                    summary[metric.platform]['sentiment_breakdown'] = {
                        'positive': (summary[metric.platform]['sentiment_breakdown'].get('positive', 0) + 
                                   (metric.positive_count or 0)),
                        'neutral': (summary[metric.platform]['sentiment_breakdown'].get('neutral', 0) + 
                                  (metric.neutral_count or 0)),
                        'negative': (summary[metric.platform]['sentiment_breakdown'].get('negative', 0) + 
                                   (metric.negative_count or 0))
                    }
                elif metric.platform == 'survey':
                    summary['survey']['avg_satisfaction'] += metric.avg_satisfaction or 0
                    summary['survey']['recommendation_rate'] += metric.recommendation_rate or 0
                    summary['survey']['total_count'] += metric.total_count or 0
            
            # Average the sentiment scores
            platform_counts = {p: 0 for p in ['twitter', 'reddit']}
            for metric in metrics:
                if metric.platform in platform_counts:
                    platform_counts[metric.platform] += 1
            
            for platform in ['twitter', 'reddit']:
                if platform_counts[platform] > 0:
                    summary[platform]['avg_sentiment'] /= platform_counts[platform]
            
            if len([m for m in metrics if m.platform == 'survey']) > 0:
                survey_count = len([m for m in metrics if m.platform == 'survey'])
                summary['survey']['avg_satisfaction'] /= survey_count
                summary['survey']['recommendation_rate'] /= survey_count
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting title summary: {e}")
            return {}
        finally:
            session.close()