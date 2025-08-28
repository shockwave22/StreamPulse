import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from config import Config
from database.models import SurveyResponse, NetflixTitle
from database.database import db_manager

logger = logging.getLogger(__name__)

class SurveyCollector:
    def __init__(self):
        self.data_dir = Config.DATA_DIR
    
    def generate_mock_survey_data(self, title: str, num_responses: int = 100) -> List[Dict]:
        """Generate mock survey data for a Netflix title"""
        np.random.seed(hash(title) % 2**32)  # Consistent random data per title
        
        survey_data = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(num_responses):
            # Generate realistic survey responses
            satisfaction_score = np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.15, 0.25, 0.35, 0.20])
            would_recommend = satisfaction_score >= 4
            completion_rate = np.random.beta(2, 1)  # Skewed towards higher completion
            
            survey_data.append({
                'respondent_id': f"resp_{title.replace(' ', '_')}_{i:04d}",
                'satisfaction_score': satisfaction_score,
                'would_recommend': would_recommend,
                'completion_rate': completion_rate,
                'created_at': base_date + timedelta(days=np.random.randint(0, 30))
            })
        
        return survey_data
    
    def load_csv_survey_data(self, file_path: str) -> List[Dict]:
        """Load survey data from CSV file"""
        try:
            df = pd.read_csv(file_path)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error loading CSV survey data: {e}")
            return []
    
    def store_survey_responses(self, title: str, survey_data: List[Dict]):
        """Store survey responses in database"""
        session = db_manager.get_session()
        try:
            # Get or create Netflix title
            netflix_title = session.query(NetflixTitle).filter_by(title=title).first()
            if not netflix_title:
                netflix_title = NetflixTitle(title=title)
                session.add(netflix_title)
                session.commit()
            
            # Store survey responses
            stored_count = 0
            for response_info in survey_data:
                # Check if response already exists
                existing_response = session.query(SurveyResponse).filter_by(
                    respondent_id=response_info['respondent_id']
                ).first()
                
                if not existing_response:
                    response = SurveyResponse(
                        title_id=netflix_title.id,
                        respondent_id=response_info['respondent_id'],
                        satisfaction_score=response_info['satisfaction_score'],
                        would_recommend=response_info['would_recommend'],
                        completion_rate=response_info['completion_rate'],
                        created_at=response_info.get('created_at', datetime.utcnow())
                    )
                    session.add(response)
                    stored_count += 1
            
            session.commit()
            logger.info(f"Stored {stored_count} new survey responses for '{title}'")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing survey responses for '{title}': {e}")
        finally:
            session.close()
    
    def generate_all_mock_data(self):
        """Generate mock survey data for all Netflix titles"""
        for title in Config.NETFLIX_TITLES:
            try:
                survey_data = self.generate_mock_survey_data(title)
                self.store_survey_responses(title, survey_data)
            except Exception as e:
                logger.error(f"Failed to generate survey data for '{title}': {e}")
                continue
    
    def create_sample_csv(self, title: str, file_path: str = None):
        """Create a sample CSV file for survey data"""
        if file_path is None:
            file_path = self.data_dir / f"{title.replace(' ', '_')}_survey.csv"
        
        survey_data = self.generate_mock_survey_data(title)
        df = pd.DataFrame(survey_data)
        df.to_csv(file_path, index=False)
        logger.info(f"Sample CSV created: {file_path}")