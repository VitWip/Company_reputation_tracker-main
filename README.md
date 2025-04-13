# Company Reputation Tracker

A Dash-powered application that tracks company mentions from news sources, analyzes sentiment using OpenAI, and presents insights through an interactive dashboard.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](#)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](#)
[![Daily Tracker](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/daily_tracker.yml/badge.svg)](#)

## Features

- **Company & Aliases** – Input multiple names or aliases for each company.  
- **News Fetching** – Pull mentions from [NewsAPI](https://newsapi.org/) for the past 7 days (configurable).  
- **Advanced Sentiment Analysis** – Leverages OpenAI's GPT-4o-mini model to label each mention as POSITIVE, NEUTRAL, or NEGATIVE, with a score between -1 and +1.  
- **Content Extraction** – Uses BeautifulSoup to retrieve full article text for more accurate analysis.  
- **Interactive Dash Dashboard** – Visualize sentiment distribution, timeline trends, and detailed mention tables in real-time.  
- **SQLite Database** – Persist all companies, aliases, and mentions in a local database.  
- **GitHub Actions Automation** – Automatically fetch and analyze new mentions every day (6:00 AM UTC) and push updates back to the repository.  
- **Comprehensive Logging** – A robust logging system tracks errors, warnings, and pipeline updates.

---

## Quick Start

### 1. Automated Setup
Run the setup script to install dependencies and initialize the database:
```bash
python setup.py
```
This will:
- Install requirements (`requirements.txt`)
- Create `company_tracker.db` if it doesn't exist
- Generate a `.env` file for storing API keys

### 2. Manual Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure `.env`**:
   Create a `.env` file in the project root with:
   ```bash
   NEWSAPI_KEY=your_newsapi_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Initialize the Database**:
   ```bash
   python db.py
   ```

---

## Usage

### Launch the Dashboard
```bash
python dashboard.py
```
Access the dashboard at [http://localhost:8050](http://localhost:8050) to view sentiment charts, recent mentions, and more.

### Command Line Operations
```bash
# Add a new company
python runner.py --add --name "Company Name" --aliases "Alias1,Alias2"

# Process a specific company (fetch & analyze mentions)
python runner.py --company 1

# List all companies in the database
python runner.py

# Run the pipeline update for all companies
python runner.py --all

# Limit the number of articles to process
python runner.py --all --limit 20
```

---

## GitHub Actions for Automated Updates

1. **Configure Secrets**:  
   - In your GitHub repo → **Settings** → **Secrets and variables** → **Actions**  
   - Add `NEWSAPI_KEY` and `OPENAI_API_KEY` as repository secrets.

2. **Daily Schedule**:  
   - The included workflow (`.github/workflows/daily_tracker.yml`) runs every day at 6:00 AM UTC:
     - Fetches & analyzes new mentions for all companies.
     - Commits the updated database or logs back to the repository.
     - Stores any run artifacts for reference.

3. **Manual Trigger**:  
   - In **Actions** → **Daily Company Reputation Tracker** → **Run workflow**.

---

## Advanced Sentiment Analysis

- **OpenAI**: By providing `OPENAI_API_KEY` in `.env`, the application uses the "gpt-4o-mini" model to analyze text sentiment.
- **Scoring**: Ranges from `-1.0` (very negative) to `1.0` (very positive).
- **Thresholds**: Mentions are labeled `POSITIVE`, `NEGATIVE`, or `NEUTRAL`.
- **Article Content**: BeautifulSoup scrapes the full body of each article to improve analysis accuracy.
- **Fallback**: If OpenAI is unavailable, a simple rule-based sentiment analyzer will be used.

---

## Project Structure

```
company_tracker/
├── api_client.py         # Fetches news and applies sentiment analysis
├── db.py                 # SQLite models & utility functions
├── dashboard.py          # Dash web application
├── runner.py             # Main script for fetching & analyzing mentions
├── setup.py              # Setup script for easy installation
├── logger.py             # Logging utilities
├── requirements.txt
├── .github/
│   └── workflows/
│       └── daily_tracker.yml  # GitHub Actions pipeline
└── README.md
```

---

## Dashboard Highlights

- **Company Selection**: Choose any tracked company from the sidebar.  
- **Sentiment Overview**: Bar chart showing distribution of POSITIVE, NEUTRAL, NEGATIVE mentions.  
- **Average Score**: Real-time gauge of sentiment performance, updated with new mentions.  
- **Sentiment Timeline**: See how sentiment changes over time, with optional trend lines.  
- **Recent Mentions**: Table of the latest articles, color-coded by sentiment.  
- **Filters**: Narrow results by date range and sentiment type.

---

## Troubleshooting

1. **API Errors**: 
   - Ensure `NEWSAPI_KEY` is correct and that you have an active internet connection.
   - Check if you've exceeded your NewsAPI daily limit (60 requests for free tier).

2. **OpenAI Errors**: 
   - If `OPENAI_API_KEY` is missing or invalid, the app falls back to a simple rule-based sentiment analyzer.
   - If you're seeing quota errors, check your OpenAI usage limits.

3. **Logs**: 
   - Check the `logs/` folder for detailed error messages and pipeline steps.
   - Most recent logs are named with the current date format (e.g., `app_20250413.log`).

4. **Minimal Installation**:
   ```bash
   pip install dash dash-bootstrap-components plotly sqlalchemy requests python-dotenv pandas openai
   ```
   *(Omits advanced libraries like BeautifulSoup, fallback mode will still function.)*

5. **Database Issues**:
   - If the database becomes corrupted, delete `company_tracker.db` and run `python db.py` to recreate it.
   - Consider making regular backups of your database if you have important data.

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

Enjoy using the **Company Reputation Tracker**!