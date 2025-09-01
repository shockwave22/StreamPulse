import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from database.database import db_manager
from database.models import NetflixTitle, AggregatedMetrics, Tweet, RedditComment
from data_aggregation.aggregator import DataAggregator
from config import Config
import logging

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="StreamPulse Dashboard",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

class StreamPulseDashboard:
    def __init__(self):
        self.aggregator = DataAggregator()
        
    def load_netflix_titles(self):
        session = db_manager.get_session()
        try:
            titles = session.query(NetflixTitle).all()
            return [title.title for title in titles]
        except Exception as e:
            logger.error(f"Error loading titles: {e}")
            return Config.NETFLIX_TITLES
        finally:
            session.close()
    
    def get_aggregated_data(self, title: str, days: int = 7):
        session = db_manager.get_session()
        try:
            netflix_title = session.query(NetflixTitle).filter_by(title=title).first()
            if not netflix_title:
                return pd.DataFrame()
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            metrics = session.query(AggregatedMetrics).filter(
                AggregatedMetrics.title_id == netflix_title.id,
                AggregatedMetrics.date >= start_date,
                AggregatedMetrics.date <= end_date
            ).all()
            data = []
            for metric in metrics:
                data.append({
                    'date': metric.date,
                    'platform': metric.platform,
                    'avg_sentiment': metric.avg_sentiment,
                    'positive_count': metric.positive_count,
                    'neutral_count': metric.neutral_count,
                    'negative_count': metric.negative_count,
                    'total_count': metric.total_count,
                    'avg_satisfaction': metric.avg_satisfaction,
                    'recommendation_rate': metric.recommendation_rate
                })
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error getting aggregated data: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def get_raw_content(self, title: str, platform: str = 'both', limit: int = 50):
        session = db_manager.get_session()
        try:
            netflix_title = session.query(NetflixTitle).filter_by(title=title).first()
            if not netflix_title:
                return pd.DataFrame()
            data = []
            if platform in ['both', 'twitter']:
                tweets = session.query(Tweet).filter_by(title_id=netflix_title.id).limit(limit).all()
                for tweet in tweets:
                    data.append({
                        'platform': 'Twitter',
                        'content': tweet.text,
                        'author': tweet.author,
                        'created_at': tweet.created_at,
                        'engagement': tweet.like_count + tweet.retweet_count
                    })
            if platform in ['both', 'reddit']:
                comments = session.query(RedditComment).filter_by(title_id=netflix_title.id).limit(limit).all()
                for comment in comments:
                    data.append({
                        'platform': 'Reddit',
                        'content': comment.text,
                        'author': comment.author,
                        'created_at': comment.created_at,
                        'engagement': comment.score
                    })
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error getting raw content: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def create_sentiment_trend_chart(self, df):
        if df.empty:
            return go.Figure()
        sentiment_df = df[df['platform'].isin(['twitter', 'reddit'])].copy()
        if sentiment_df.empty:
            return go.Figure()
        fig = px.line(
            sentiment_df,
            x='date',
            y='avg_sentiment',
            color='platform',
            title='Sentiment Trend Over Time',
            labels={'avg_sentiment': 'Average Sentiment Score', 'date': 'Date'}
        )
        fig.update_layout(
            hovermode='x unified',
            yaxis_range=[-1, 1]
        )
        return fig
    
    def create_sentiment_distribution_chart(self, df):
        if df.empty:
            return go.Figure()
        sentiment_data = []
        for platform in ['twitter', 'reddit']:
            platform_data = df[df['platform'] == platform]
            if not platform_data.empty:
                sentiment_data.append({
                    'platform': platform.title(),
                    'positive': platform_data['positive_count'].sum(),
                    'neutral': platform_data['neutral_count'].sum(),
                    'negative': platform_data['negative_count'].sum()
                })
        if not sentiment_data:
            return go.Figure()
        sentiment_df = pd.DataFrame(sentiment_data)
        fig = go.Figure()
        # Updated colors: green for positive, blue for neutral, red for negative
        sentiment_color_map = {'positive': '#4CAF50', 'neutral': '#2196F3', 'negative': '#F44336'}
        for sentiment in ['positive', 'neutral', 'negative']:
            fig.add_trace(go.Bar(
                name=sentiment.title(),
                x=sentiment_df['platform'],
                y=sentiment_df[sentiment],
                marker_color=sentiment_color_map[sentiment]
            ))
        fig.update_layout(
            title='Sentiment Distribution by Platform',
            barmode='stack',
            xaxis_title='Platform',
            yaxis_title='Number of Posts/Comments'
        )
        return fig
    
    def create_survey_comparison_chart(self, df):
        if df.empty:
            return go.Figure()
        survey_data = df[df['platform'] == 'survey']
        social_data = df[df['platform'].isin(['twitter', 'reddit'])]
        if survey_data.empty or social_data.empty:
            return go.Figure()
        avg_satisfaction = survey_data['avg_satisfaction'].mean()
        avg_social_sentiment = social_data['avg_sentiment'].mean()
        recommendation_rate = survey_data['recommendation_rate'].mean()
        normalized_satisfaction = (avg_satisfaction - 3) / 2
        comparison_data = pd.DataFrame({
            'Metric': ['Survey Satisfaction', 'Social Sentiment', 'Recommendation Rate'],
            'Score': [normalized_satisfaction, avg_social_sentiment, recommendation_rate * 2 - 1]
        })
        fig = px.bar(
            comparison_data,
            x='Metric',
            y='Score',
            title='Survey vs Social Media Sentiment Comparison',
            color='Score',
            color_continuous_scale='RdYlGn',
            range_color=[-1, 1]
        )
        fig.update_layout(yaxis_range=[-1, 1])
        return fig
    
    def create_wordcloud(self, title: str):
        content_df = self.get_raw_content(title, limit=100)
        if content_df.empty:
            return None
        text = ' '.join(content_df['content'].astype(str))
        wordcloud = WordCloud(
            width=800, 
            height=400, 
            background_color='white',
            max_words=100,
            colormap='viridis'
        ).generate(text)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        return fig
    
    def run_dashboard(self):
        st.title("📺 StreamPulse: Netflix Sentiment Dashboard")

        # Professional, readable, modern intro box
        st.markdown("""
        <div style="
            background-color: #e6f2fa;
            padding: 20px 24px;
            border-radius: 10px;
            margin-bottom: 24px;
            border-left: 5px solid #2196F3;
        ">
            <span style="color: #222; font-size: 1.15rem;">
            <strong>StreamPulse</strong> is a real-time analytics dashboard focused on consumer sentiment for Netflix original content.<br>
            This app continuously collects audience reactions from Twitter, Reddit, and viewer surveys. Using advanced sentiment analysis, it highlights trends, engagement, and key themes for every tracked Netflix show or movie.<br>
            Explore how audiences feel about your favorite titles, compare survey results with social media sentiment, and discover what drives viewer satisfaction.
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("Real-time consumer sentiment analysis for Netflix original content")
        # ... [rest of your dashboard code]
        
        # Sidebar
        st.sidebar.header("Filters")
        titles = self.load_netflix_titles()
        selected_title = st.sidebar.selectbox("Select Netflix Title", titles)
        days_back = st.sidebar.slider("Days to analyze", 1, 30, 7)
        platform_filter = st.sidebar.selectbox(
            "Platform Filter",
            ["All", "Twitter", "Reddit", "Survey"]
        )
        if st.sidebar.button("🔄 Refresh Data"):
            st.rerun()
        df = self.get_aggregated_data(selected_title, days_back)
        if df.empty:
            st.warning(f"No data available for '{selected_title}'. Please check data collection.")
            return
        if platform_filter != "All":
            df = df[df['platform'] == platform_filter.lower()]
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", 
            "📈 Trends", 
            "🔍 Comparison", 
            "☁️ Keywords", 
            "💬 Raw Data"
        ])
        with tab1:
            st.header(f"Overview: {selected_title}")
            col1, col2, col3, col4 = st.columns(4)
            total_posts = df['total_count'].sum()
            avg_sentiment = df[df['platform'].isin(['twitter', 'reddit'])]['avg_sentiment'].mean()
            survey_satisfaction = df[df['platform'] == 'survey']['avg_satisfaction'].mean()
            recommendation_rate = df[df['platform'] == 'survey']['recommendation_rate'].mean()
            with col1:
                st.metric("Total Posts/Comments", f"{total_posts:,}")
            with col2:
                sentiment_color = "normal" if -0.1 <= avg_sentiment <= 0.1 else ("inverse" if avg_sentiment > 0.1 else "off")
                st.metric("Average Sentiment", f"{avg_sentiment:.2f}", delta_color=sentiment_color)
            with col3:
                if not pd.isna(survey_satisfaction):
                    st.metric("Survey Satisfaction", f"{survey_satisfaction:.1f}/5")
                else:
                    st.metric("Survey Satisfaction", "No data")
            with col4:
                if not pd.isna(recommendation_rate):
                    st.metric("Recommendation Rate", f"{recommendation_rate:.1%}")
                else:
                    st.metric("Recommendation Rate", "No data")
            st.plotly_chart(self.create_sentiment_distribution_chart(df), use_container_width=True)
        with tab2:
            st.header("Sentiment Trends Over Time")
            st.plotly_chart(self.create_sentiment_trend_chart(df), use_container_width=True)
            col1, col2 = st.columns(2)
            with col1:
                twitter_data = df[df['platform'] == 'twitter']
                if not twitter_data.empty:
                    st.subheader("Twitter Metrics")
                    st.metric("Total Tweets", twitter_data['total_count'].sum())
                    st.metric("Avg Sentiment", f"{twitter_data['avg_sentiment'].mean():.2f}")
            with col2:
                reddit_data = df[df['platform'] == 'reddit']
                if not reddit_data.empty:
                    st.subheader("Reddit Metrics")
                    st.metric("Total Comments", reddit_data['total_count'].sum())
                    st.metric("Avg Sentiment", f"{reddit_data['avg_sentiment'].mean():.2f}")
        with tab3:
            st.header("Survey vs Social Media Comparison")
            st.plotly_chart(self.create_survey_comparison_chart(df), use_container_width=True)
            st.subheader("Key Insights")
            survey_data = df[df['platform'] == 'survey']
            social_data = df[df['platform'].isin(['twitter', 'reddit'])]
            if not survey_data.empty and not social_data.empty:
                survey_avg = survey_data['avg_satisfaction'].mean()
                social_avg = social_data['avg_sentiment'].mean()
                if abs(social_avg) < 0.1:
                    social_sentiment = "neutral"
                elif social_avg > 0.1:
                    social_sentiment = "positive"
                else:
                    social_sentiment = "negative"
                st.write(f"- Survey satisfaction: {survey_avg:.1f}/5")
                st.write(f"- Social media sentiment: {social_sentiment} ({social_avg:.2f})")
                if survey_avg > 3.5 and social_avg > 0.1:
                    st.success("✅ Positive alignment: High satisfaction and positive social sentiment")
                elif survey_avg < 2.5 and social_avg < -0.1:
                    st.error("❌ Negative alignment: Low satisfaction and negative social sentiment")
                else:
                    st.warning("⚠️ Mixed signals: Survey and social sentiment don't align")
        with tab4:
            st.header("Top Keywords and Themes")
            try:
                wordcloud_fig = self.create_wordcloud(selected_title)
                if wordcloud_fig:
                    st.pyplot(wordcloud_fig)
                else:
                    st.info("No content available for word cloud generation")
            except Exception as e:
                st.error(f"Error generating word cloud: {e}")
        with tab5:
            st.header("Raw Social Media Content")
            raw_platform = st.selectbox("Select Platform", ["Both", "Twitter", "Reddit"])
            content_limit = st.slider("Number of posts to show", 10, 100, 25)
            raw_df = self.get_raw_content(
                selected_title, 
                raw_platform.lower() if raw_platform != "Both" else "both",
                content_limit
            )
            if not raw_df.empty:
                raw_df = raw_df.sort_values('engagement', ascending=False)
                st.subheader(f"Recent Posts ({len(raw_df)} items)")
                for idx, row in raw_df.iterrows():
                    with st.expander(f"{row['platform']} - @{row['author']} ({row['engagement']} engagement)"):
                        st.write(row['content'])
                        st.caption(f"Posted: {row['created_at']}")
            else:
                st.info("No raw content available for the selected filters")
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        with col2:
            st.caption("📡 Data sources: Twitter, Reddit, Survey")
        with col3:
            if st.button("🔄 Force Data Refresh"):
                with st.spinner("Refreshing aggregated data..."):
                    self.aggregator.aggregate_daily_sentiment()
                st.success("Data refreshed successfully!")

if __name__ == "__main__":
    dashboard = StreamPulseDashboard()
    dashboard.run_dashboard()