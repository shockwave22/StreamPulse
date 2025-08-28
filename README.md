# 📺 StreamPulse: Netflix Sentiment Dashboard

A comprehensive data pipeline and dashboard application that ingests social media data and survey data, performs sentiment analysis, and displays consumer insights about Netflix original content over time.

## 🚀 Features

- **Multi-Platform Data Ingestion**: Twitter, Reddit, and Survey data collection
- **Advanced Sentiment Analysis**: VADER and Transformer-based models
- **Real-time Dashboard**: Interactive Streamlit interface
- **Automated Pipeline**: Airflow orchestration for scheduled data processing
- **Comprehensive Analytics**: Trend analysis, comparison views, and keyword insights

## 📋 Requirements

- Python 3.9+
- PostgreSQL (optional, SQLite included for development)
- Twitter Developer Account
- Reddit API Access

## 🛠️ Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/shockwave22/StreamPulse.git
cd StreamPulse

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with your API credentials:

```bash
# Database
DATABASE_URL=sqlite:///streampulse.db

# Twitter API
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# Reddit API
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
```

### 3. Initialize and Run

```bash
# Setup database and collect initial data
python main.py --full

# Start the dashboard
streamlit run dashboard/app.py
```

The dashboard will be available at `http://localhost:8501`

## 🐳 Docker Deployment

```bash
# Start all services
docker-compose up -d

# Access dashboard at http://localhost:8501
# Access Airflow at http://localhost:8080
```

## 📊 Dashboard Features

### Overview Tab
- Total posts/comments metrics
- Average sentiment scores
- Survey satisfaction ratings
- Sentiment distribution charts

### Trends Tab
- Sentiment trends over time
- Platform-specific breakdowns
- Interactive time series visualizations

### Comparison Tab
- Survey vs social media sentiment
- Alignment analysis
- Key insights and recommendations

### Keywords Tab
- Word clouds from recent content
- Top trending keywords
- Theme analysis

### Raw Data Tab
- Recent tweets and comments
- Engagement metrics
- Content filtering options

## 🔄 Data Pipeline

The pipeline consists of four main stages:

1. **Data Ingestion**: Collect data from Twitter, Reddit, and survey sources
2. **Sentiment Analysis**: Process text using VADER or transformer models
3. **Data Aggregation**: Calculate daily metrics and trends
4. **Dashboard Update**: Refresh visualizations and insights

### Scheduled Pipeline (Airflow)

The pipeline runs automatically every 6 hours:
- Fetch new social media content
- Process sentiment analysis
- Update aggregated metrics
- Refresh dashboard data

## 📁 Project Structure

```
StreamPulse/
├── config.py                 # Configuration settings
├── main.py                   # Main application entry point
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Multi-service deployment
├── database/
│   ├── models.py            # SQLAlchemy models
│   └── database.py          # Database connection
├── data_ingestion/
│   ├── twitter_collector.py # Twitter API integration
│   ├── reddit_collector.py  # Reddit API integration
│   └── survey_collector.py  # Survey data handling
├── sentiment_analysis/
│   └── analyzer.py          # Sentiment analysis engine
├── data_aggregation/
│   └── aggregator.py        # Data aggregation logic
├── dashboard/
│   └── app.py               # Streamlit dashboard
├── airflow_dags/
│   └── streampulse_pipeline.py # Airflow DAG
├── data/                    # Data storage directory
└── logs/                    # Application logs
```

## 🔧 Configuration

### Netflix Titles Tracked
- Stranger Things
- The Witcher
- Wednesday
- Ozark
- The Crown
- Bridgerton
- Squid Game
- Money Heist
- Dark
- The Umbrella Academy

### Sentiment Analysis Models
- **VADER**: Rule-based sentiment analysis (default)
- **Transformers**: DistilBERT fine-tuned model (optional)

## 📈 Usage Examples

### Manual Data Collection
```bash
# Collect data for specific operations
python main.py --collect    # Collect new data
python main.py --sentiment  # Process sentiment
python main.py --aggregate  # Update aggregations
```

### API Integration
```python
from data_ingestion.twitter_collector import TwitterCollector

collector = TwitterCollector()
tweets = collector.collect_tweets_for_title("Stranger Things", max_results=50)
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run specific test modules
pytest tests/test_sentiment_analysis.py
pytest tests/test_data_ingestion.py
```

## 🔒 Security Considerations

- Store API credentials in environment variables
- Use read-only database credentials for dashboard
- Implement rate limiting for API calls
- Regular security updates for dependencies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**Database Connection Errors**
- Verify DATABASE_URL in .env file
- Ensure PostgreSQL is running (if using)
- Check database permissions

**API Rate Limits**
- Monitor API usage in logs
- Implement longer delays between requests
- Consider upgrading API plans

**Dashboard Not Loading**
- Check if all dependencies are installed
- Verify Streamlit is running on correct port
- Review application logs for errors

### Getting Help

- Check the [Issues](https://github.com/shockwave22/StreamPulse/issues) page
- Review logs in the `logs/` directory
- Enable debug logging: `LOG_LEVEL=DEBUG`

## 📊 Performance Tips

- Use PostgreSQL for production deployments
- Configure database connection pooling
- Implement caching for dashboard data
- Monitor memory usage with large datasets
- Use batch processing for sentiment analysis

---

**Built with ❤️ by the StreamPulse Team**