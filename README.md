# LinkedIn AI Talent Outreach System 🤖

A comprehensive full-stack automation system for LinkedIn talent outreach, featuring AI-powered message generation, intelligent target discovery, viral content creation, and detailed analytics.

## 🎯 Overview

This system automates the process of discovering and connecting with India-based AI hiring managers at top tech companies. It uses local LLMs (via Ollama) for personalized message generation, analyzes viral content patterns, and provides detailed analytics through a web dashboard.

## ✨ Key Features

- **🔍 Smart Target Discovery**: Automatically finds India-based AI hiring managers
- **🤖 AI-Powered Personalization**: Uses Ollama for personalized messages
- **⚡ Smart Automation**: Respects LinkedIn's 30 connections/day limit
- **📊 Analytics Dashboard**: Comprehensive tracking and metrics
- **🔥 Viral Content Generation**: AI-powered post creation and analysis

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/Mudit7715/linkedin_ai_outreach.git
cd linkedin_ai_outreach

# Run quick start script
./quickstart.sh
```

The script will:
1. Set up environment and dependencies
2. Initialize the database
3. Start the dashboard at http://localhost:8501

## 📋 Prerequisites

- Python 3.11+
- Chrome/Chromium browser
- ChromeDriver (matching your Chrome version)
- Ollama installed and running
- LinkedIn account

## 🛠️ Installation

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

### 2. Setup Ollama

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
ollama serve

# Pull required model
ollama pull llama2
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
vim .env
```

Required environment variables:
- `LINKEDIN_EMAIL`: Your LinkedIn email
- `LINKEDIN_PASSWORD`: Your LinkedIn password
- `OLLAMA_BASE_URL`: Ollama API endpoint

## 💻 Usage

### Start the Dashboard

```bash
streamlit run ui/dashboard.py
```

The dashboard provides:
- Pipeline status overview
- Message queue management
- Analytics and metrics
- Viral post management
- Prompt configuration
- System settings

### Start Automation

```bash
# In a separate terminal
python -m linkedin_ai_outreach.core.automation_scheduler
```

This runs:
- Nightly target discovery (2 AM)
- Morning viral post generation (7 AM)
- Continuous connection management
- Message scheduling with 5-hour delay

## 🐳 Docker Support

```bash
# Start all services
docker-compose up -d

# View dashboard
open http://localhost:8501
```

Services:
- `ollama`: Local LLM server
- `automation`: Main automation service
- `dashboard`: Web interface
- `selenium`: Browser automation grid

## 📊 Analytics

The system tracks:
- Connection acceptance rates
- Message reply rates
- Company-wise engagement
- Viral post performance
- Daily activity metrics

## ⚙️ Configuration

Key configuration files:
- `config/prompts.yml`: AI prompt templates
- `.env`: Environment variables
- `docker-compose.yml`: Container configuration

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Quick system check
python test_system.py
```

## 🔒 Security Notes

- Credentials are stored in `.env` (never commit this file)
- Database is local SQLite (can be changed in production)
- All automation respects LinkedIn's rate limits
- Messages are generated locally via Ollama

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📖 License

This project is for educational purposes. Ensure compliance with LinkedIn's Terms of Service and local regulations when using automation tools.

## 🆘 Support

- Check the troubleshooting section
- Review code documentation
- Open an issue on GitHub

---

**Note**: This system is designed for professional networking and career development. Always use it ethically and in compliance with platform terms of service.

## 🚀 Features

### Core Functionality
- **Intelligent Target Discovery**: Automatically discovers India-based AI hiring managers at top tech companies
- **AI-Powered Personalization**: Uses Ollama (local LLM) to generate highly personalized connection requests and messages
- **Smart Automation**: Respects LinkedIn limits (30 connections/day) with human-like timing
- **Viral Content Generation**: Analyzes trending AI posts and generates engaging content
- **Comprehensive Analytics**: Track acceptance rates, reply rates, and outreach effectiveness

### Key Components
1. **Data Scraper**: Discovers and profiles potential connections
2. **Message Generator**: Creates personalized outreach using profile analysis
3. **Viral Post Miner**: Identifies trending AI content patterns
4. **Automation Scheduler**: Orchestrates all activities with smart timing
5. **Web Dashboard**: Full-featured UI for monitoring and control

## 📋 Prerequisites

- Python 3.11+
- Chrome/Chromium browser
- ChromeDriver (matching your Chrome version)
- Ollama installed and running
- LinkedIn account

## 🛠️ Installation

### 1. Clone the repository
```bash
cd ~/linkedin_ai_outreach
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Install and setup Ollama
```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
ollama serve

# Pull a model (e.g., llama2)
ollama pull llama2
```

### 4. Install ChromeDriver
```bash
# macOS
brew install chromedriver

# Or download from https://chromedriver.chromium.org/
```

### 5. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your LinkedIn credentials and settings
```

## 🚦 Quick Start

### 1. Start the Web Dashboard
```bash
streamlit run ui/dashboard.py
```
The dashboard will open at http://localhost:8501

### 2. Initial Setup in Dashboard
1. Go to **Settings** and verify Ollama is running
2. Check **Prompt Editor** to review/customize prompts
3. Navigate to **Dashboard** to see system status

### 3. Run Your First Scraper
1. Click **🔍 Run Scraper** in Settings
2. The system will discover AI professionals from target companies
3. View discovered targets in **Pipeline Status**

### 4. Start Automation
```bash
# In a separate terminal, run the scheduler
python -m linkedin_ai_outreach.core.automation_scheduler
```

## 📁 Project Structure

```
linkedin_ai_outreach/
├── core/
│   ├── enhanced_tracker.py      # Database and tracking logic
│   ├── ollama_connector.py      # LLM integration
│   └── automation_scheduler.py  # Main automation engine
├── scrapers/
│   ├── linkedin_scraper.py      # Profile discovery and scraping
│   └── viral_post_miner.py      # Trending content analysis
├── ui/
│   └── dashboard.py             # Streamlit web interface
├── config/
│   └── prompts.yml             # Editable prompt templates
├── data/                       # Data storage directory
├── tests/                      # Unit tests
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
└── README.md                  # This file
```

## 🎯 Usage Guide

### Daily Workflow

1. **Morning (7 AM)**: System generates viral post based on trending content
2. **Throughout Day**: Sends up to 30 connection requests with personalization
3. **Every 15 min**: Checks for accepted connections
4. **After 5 hours**: Sends personalized follow-up messages
5. **Night (2 AM)**: Discovers new targets from configured companies

### Dashboard Features

#### 📊 Dashboard
- Overview of all metrics
- Outreach funnel visualization
- Quick action buttons

#### 🎯 Pipeline Status
- View all targets by status
- Manual status updates
- Opt-out management

#### 📮 Message Queue
- See pending messages
- Process message queue manually
- View message history

#### 📈 Analytics
- Time series analysis
- Company breakdown
- Success rate tracking

#### 🔥 Viral Posts
- Approve/reject generated posts
- Generate new posts on-demand
- View published post performance

#### ⚙️ Prompt Editor
- Edit all system prompts
- Test generation with custom inputs
- Hot-reload capability

## 🔧 Configuration

### Prompts Configuration (config/prompts.yml)

The system uses customizable prompts for all AI generation:
- Connection requests
- Personalized messages
- Viral post creation
- Profile analysis

Edit these in the UI or directly in the YAML file.

### Target Companies

Configure target companies in `prompts.yml`:
```yaml
target_companies:
  global_leaders:
    - Google
    - Microsoft
    - OpenAI
    # Add more...
  india_presence:
    - Google India
    - Microsoft India
    # Add more...
```

## 🚨 Important Considerations

### LinkedIn Terms of Service
- This tool automates LinkedIn activities. Use responsibly.
- Respect rate limits and human-like behavior
- The connection limit (30/day) is enforced by the system

### Privacy & Ethics
- Only uses publicly available information
- Includes opt-out functionality
- Stores data locally in SQLite

### Safety Features
- Rate limiting built-in
- Random delays between actions
- Daily limit enforcement
- Manual approval for posts

## 🧪 Testing

Run tests with:
```bash
pytest tests/
```

## 🐛 Troubleshooting

### Ollama not running
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

### ChromeDriver issues
- Ensure ChromeDriver version matches Chrome browser
- Add ChromeDriver to PATH or specify in .env

### Database issues
```bash
# Reset database (WARNING: deletes all data)
rm linkedin_ai_outreach.db
python -c "from core.enhanced_tracker import EnhancedLinkedInTracker; EnhancedLinkedInTracker()"
```

## 📝 Development

### Adding New Features
1. Extend the database schema in `enhanced_tracker.py`
2. Add new prompts in `prompts.yml`
3. Create UI components in `dashboard.py`
4. Add scheduling logic in `automation_scheduler.py`

### Code Style
```bash
# Format code
black .

# Lint
flake8 .
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is for educational purposes. Ensure compliance with LinkedIn's Terms of Service and local regulations when using automation tools.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the code documentation
3. Open an issue on GitHub

---

**Note**: This system is designed for professional networking and career development. Always use it ethically and in compliance with platform terms of service.
