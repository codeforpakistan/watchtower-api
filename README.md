# 🏛️ Watchtower API

> Holding government institutions accountable through automated website performance and quality analysis.

## Overview

Watchtower is a FastAPI-based service that monitors and evaluates government websites to ensure taxpayer money is being used effectively for digital services. The API automatically scans government websites, analyzes their performance using Google PageSpeed Insights, and critiques their design and content using AI-powered analysis.

## 🎯 Mission

Government websites should serve citizens effectively. Watchtower provides transparency by:
- **Performance Monitoring**: Tracking load times, accessibility, and technical performance
- **AI-Powered Critique**: Analyzing design quality, content clarity, and user experience
- **Public Accountability**: Creating leaderboards to highlight best and worst performers
- **Data-Driven Insights**: Providing actionable feedback for improvement

## 🛠️ Tech Stack

- **API Framework**: FastAPI
- **Package Management**: Poetry
- **Database**: Supabase (PostgreSQL)
- **Performance Analysis**: Google PageSpeed Insights API
- **Web Crawling**: Playwright
- **AI Analysis**: OpenAI/Anthropic APIs
- **Python Version**: 3.11+

## 🚀 Features

### Core Functionality
- **Website Registry**: Maintain a database of government websites to monitor
- **Automated Scanning**: Scheduled performance and quality assessments
- **Performance Metrics**: PageSpeed Insights integration for Core Web Vitals
- **AI Content Analysis**: Automated critique of design, accessibility, and content quality
- **Leaderboard System**: Ranking websites from best to worst performers
- **Historical Tracking**: Monitor improvements or degradation over time

### API Endpoints
- `GET /websites` - List all monitored government websites
- `POST /websites` - Add new website to monitoring
- `GET /websites/{id}/reports` - Get analysis reports for a specific website
- `GET /leaderboard` - View ranked performance leaderboard
- `POST /scan/{id}` - Trigger manual scan of a website
- `GET /metrics` - Overall system metrics and statistics

## 📊 Analysis Criteria

### Performance Metrics
- **Core Web Vitals**: LCP, FID, CLS scores
- **PageSpeed Score**: Overall performance rating
- **Accessibility**: WCAG compliance assessment
- **Best Practices**: Security and modern web standards

### AI Quality Assessment
- **Design Quality**: Visual hierarchy, modern design principles
- **Content Clarity**: Language accessibility, information architecture
- **User Experience**: Navigation, mobile responsiveness
- **Accessibility**: Screen reader compatibility, color contrast
- **Government Standards**: Compliance with digital service standards

## 🏗️ Project Structure

```
watchtower-api/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── websites.py
│   │   │   ├── reports.py
│   │   │   └── leaderboard.py
│   │   └── deps.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/
│   │   ├── website.py
│   │   ├── report.py
│   │   └── analysis.py
│   ├── services/
│   │   ├── pagespeed.py
│   │   ├── crawler.py
│   │   ├── ai_analyzer.py
│   │   └── scheduler.py
│   └── main.py
├── tests/
├── scripts/
├── pyproject.toml
├── README.md
└── .env.example
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.11+
- Poetry
- Supabase account
- Google PageSpeed Insights API key
- OpenAI/Anthropic API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/codeforpakistan/watchtower-api.git
   cd watchtower-api
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Environment setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Database setup**
   ```bash
   poetry run python scripts/init_db.py
   ```

5. **Run the application**
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

## ⚙️ Configuration

### Environment Variables

```env
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# APIs
GOOGLE_PAGESPEED_API_KEY=your_pagespeed_api_key
OPENAI_API_KEY=your_openai_api_key

# Application
API_V1_STR=/api/v1
PROJECT_NAME=Watchtower API
DEBUG=False

# Scheduling
SCAN_INTERVAL_HOURS=24
MAX_CONCURRENT_SCANS=5
```

## 📊 Database Schema

### Tables

**websites**
- `id` (UUID, Primary Key)
- `name` (Text) - Website/Agency name
- `url` (Text) - Website URL
- `government_level` (Enum) - Federal, State, Local
- `agency_type` (Text) - Department, Municipality, etc.
- `created_at` (Timestamp)
- `last_scanned` (Timestamp)

**reports**
- `id` (UUID, Primary Key)
- `website_id` (UUID, Foreign Key)
- `scan_date` (Timestamp)
- `pagespeed_score` (Integer)
- `core_web_vitals` (JSONB)
- `ai_analysis` (JSONB)
- `overall_score` (Float)

## 🤖 AI Analysis Framework

The AI analysis evaluates websites across multiple dimensions:

1. **Accessibility Score** (0-100)
   - Color contrast ratios
   - Alt text presence
   - Keyboard navigation
   - Screen reader compatibility

2. **Design Quality Score** (0-100)
   - Visual hierarchy
   - Modern design principles
   - Consistency
   - Professional appearance

3. **Content Quality Score** (0-100)
   - Language clarity
   - Information findability
   - Content organization
   - Citizen-focused messaging

4. **Overall Usability Score** (0-100)
   - Combined weighted score
   - Benchmarked against best practices

## 📈 API Usage Examples

### Adding a new website to monitor
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/websites",
    json={
        "name": "Department of Motor Vehicles",
        "url": "https://dmv.example.gov",
        "government_level": "state",
        "agency_type": "department"
    }
)
```

### Getting the leaderboard
```python
leaderboard = requests.get("http://localhost:8000/api/v1/leaderboard")
print(leaderboard.json())
```

## 🔄 Deployment

### Docker Deployment
```bash
docker build -t watchtower-api .
docker run -p 8000:8000 --env-file .env watchtower-api
```

### Production Considerations
- Set up proper logging and monitoring
- Configure rate limiting for external APIs
- Implement caching for frequently accessed data
- Set up automated backups for Supabase
- Use environment-specific configurations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

- [ ] **Phase 1**: Core API with basic scanning
- [ ] **Phase 2**: AI analysis integration
- [ ] **Phase 3**: Public dashboard and leaderboards
- [ ] **Phase 4**: Automated reporting and alerts
- [ ] **Phase 5**: Historical trend analysis
- [ ] **Phase 6**: Cost-effectiveness analysis

## 📞 Support

For questions, suggestions, or issues:
- Create an issue on GitHub
- Email: [your-email@example.com]
- Twitter: [@watchtower_gov]

---

*Empowering citizens through government website transparency and accountability.*