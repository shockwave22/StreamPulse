from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class NetflixTitle(Base):
    __tablename__ = 'netflix_titles'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tweets = relationship("Tweet", back_populates="title")
    reddit_comments = relationship("RedditComment", back_populates="title")
    survey_responses = relationship("SurveyResponse", back_populates="title")

class Tweet(Base):
    __tablename__ = 'tweets'
    
    id = Column(Integer, primary_key=True)
    tweet_id = Column(String(50), unique=True, nullable=False)
    title_id = Column(Integer, ForeignKey('netflix_titles.id'))
    text = Column(Text, nullable=False)
    author = Column(String(255))
    created_at = Column(DateTime, nullable=False)
    retweet_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    
    # Relationships
    title = relationship("NetflixTitle", back_populates="tweets")
    sentiment_scores = relationship("SentimentScore", back_populates="tweet")

class RedditComment(Base):
    __tablename__ = 'reddit_comments'
    
    id = Column(Integer, primary_key=True)
    comment_id = Column(String(50), unique=True, nullable=False)
    title_id = Column(Integer, ForeignKey('netflix_titles.id'))
    text = Column(Text, nullable=False)
    author = Column(String(255))
    subreddit = Column(String(255))
    score = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False)
    
    # Relationships
    title = relationship("NetflixTitle", back_populates="reddit_comments")
    sentiment_scores = relationship("SentimentScore", back_populates="reddit_comment")

class SurveyResponse(Base):
    __tablename__ = 'survey_responses'
    
    id = Column(Integer, primary_key=True)
    title_id = Column(Integer, ForeignKey('netflix_titles.id'))
    respondent_id = Column(String(100))
    satisfaction_score = Column(Integer)  # 1-5 Likert scale
    would_recommend = Column(Boolean)
    completion_rate = Column(Float)  # 0-1
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    title = relationship("NetflixTitle", back_populates="survey_responses")

class SentimentScore(Base):
    __tablename__ = 'sentiment_scores'
    
    id = Column(Integer, primary_key=True)
    tweet_id = Column(Integer, ForeignKey('tweets.id'), nullable=True)
    reddit_comment_id = Column(Integer, ForeignKey('reddit_comments.id'), nullable=True)
    
    # Sentiment analysis results
    polarity_score = Column(Float, nullable=False)  # -1 to 1
    sentiment_class = Column(String(20), nullable=False)  # positive, neutral, negative
    confidence_score = Column(Float)  # 0 to 1
    model_used = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tweet = relationship("Tweet", back_populates="sentiment_scores")
    reddit_comment = relationship("RedditComment", back_populates="sentiment_scores")

class AggregatedMetrics(Base):
    __tablename__ = 'aggregated_metrics'
    
    id = Column(Integer, primary_key=True)
    title_id = Column(Integer, ForeignKey('netflix_titles.id'))
    platform = Column(String(50))  # twitter, reddit, survey
    date = Column(DateTime, nullable=False)
    
    # Aggregated sentiment metrics
    avg_sentiment = Column(Float)
    positive_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    
    # Survey-specific metrics
    avg_satisfaction = Column(Float)
    avg_completion_rate = Column(Float)
    recommendation_rate = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    title = relationship("NetflixTitle")