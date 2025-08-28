import praw
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from config import Config
from database.models import RedditComment, NetflixTitle
from database.database import db_manager
from retry import retry

logger = logging.getLogger(__name__)

class RedditCollector:
    def __init__(self):
        self.reddit = self._setup_reddit_api()
    
    def _setup_reddit_api(self):
        """Initialize Reddit API client"""
        try:
            reddit = praw.Reddit(
                client_id=Config.REDDIT_CLIENT_ID,
                client_secret=Config.REDDIT_CLIENT_SECRET,
                user_agent=Config.REDDIT_USER_AGENT
            )
            logger.info("Reddit API client initialized successfully")
            return reddit
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API: {e}")
            raise
    
    @retry(tries=3, delay=5, backoff=2)
    def collect_comments_for_title(self, title: str, subreddits: List[str] = None) -> List[Dict]:
        """Collect Reddit comments for a specific Netflix title"""
        if subreddits is None:
            subreddits = ['netflix', 'television', 'NetflixBestOf', 'streaming']
        
        comment_data = []
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search for posts about the title
                search_results = subreddit.search(title, time_filter='week', limit=10)
                
                for submission in search_results:
                    # Get comments from the submission
                    submission.comments.replace_more(limit=0)
                    comments = submission.comments.list()[:Config.REDDIT_COMMENTS_LIMIT]
                    
                    for comment in comments:
                        if hasattr(comment, 'body') and len(comment.body) > 10:
                            comment_data.append({
                                'comment_id': comment.id,
                                'text': comment.body,
                                'author': str(comment.author) if comment.author else '[deleted]',
                                'subreddit': subreddit_name,
                                'score': comment.score,
                                'created_at': datetime.fromtimestamp(comment.created_utc)
                            })
                
            except Exception as e:
                logger.error(f"Error collecting from r/{subreddit_name} for '{title}': {e}")
                continue
        
        logger.info(f"Collected {len(comment_data)} comments for '{title}'")
        return comment_data
    
    def store_comments(self, title: str, comment_data: List[Dict]):
        """Store collected comments in database"""
        session = db_manager.get_session()
        try:
            # Get or create Netflix title
            netflix_title = session.query(NetflixTitle).filter_by(title=title).first()
            if not netflix_title:
                netflix_title = NetflixTitle(title=title)
                session.add(netflix_title)
                session.commit()
            
            # Store comments
            stored_count = 0
            for comment_info in comment_data:
                # Check if comment already exists
                existing_comment = session.query(RedditComment).filter_by(
                    comment_id=comment_info['comment_id']
                ).first()
                
                if not existing_comment:
                    comment = RedditComment(
                        comment_id=comment_info['comment_id'],
                        title_id=netflix_title.id,
                        text=comment_info['text'],
                        author=comment_info['author'],
                        subreddit=comment_info['subreddit'],
                        score=comment_info['score'],
                        created_at=comment_info['created_at']
                    )
                    session.add(comment)
                    stored_count += 1
            
            session.commit()
            logger.info(f"Stored {stored_count} new comments for '{title}'")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing comments for '{title}': {e}")
        finally:
            session.close()
    
    def collect_all_titles(self):
        """Collect comments for all Netflix titles"""
        for title in Config.NETFLIX_TITLES:
            try:
                comment_data = self.collect_comments_for_title(title)
                self.store_comments(title, comment_data)
            except Exception as e:
                logger.error(f"Failed to collect comments for '{title}': {e}")
                continue