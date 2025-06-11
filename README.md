# Twitter Job Market Analyzer

A comprehensive Python-based solution for scraping, analyzing, and reporting on Twitter job market data. This project provides automated data collection, sentiment analysis, and professional reporting capabilities for job-related social media insights.

---

## 🚀 Project Overview

This project consists of three main components:

- **Data Collection**: Automated Twitter scraping for job-related content  
- **Data Analysis**: Sentiment, engagement, and keyword analysis with visualizations  
- **Professional Reporting**: PDF reports with embedded charts

---

## 📊 Features

- ✅ Scrapes 2000+ tweets with job-related hashtags  
- ✅ Sentiment analysis (positive, negative, neutral)  
- ✅ Engagement tracking: likes, retweets, replies, views  
- ✅ Temporal analysis: peak times & trends  
- ✅ PDF report with visual charts and executive summary  
- ✅ 12-Panel analytics dashboard  

---

## 🛠️ Technology Stack

- **Python 3.7+**
- Selenium WebDriver
- Pandas
- TextBlob
- Matplotlib
- ReportLab
- NumPy

---

---

## 🔧 Installation

```bash
git clone https://github.com/sadhyarshi/twitter-job-market-analyzer.git
cd twitter-job-market-analyzer
pip install -r requirements.txt
Install additional dependencies:

bash
Copy
Edit
pip install selenium pandas webdriver-manager textblob matplotlib reportlab numpy
🚀 Quick Start
Step 1: Data Collection

bash
Copy
Edit
python scripts/twitter_scraper.py
Collects 2000 tweets with job-related hashtags

Step 2: Analysis & Visualization

bash
Copy
Edit
python scripts/comprehensive_analysis.py
Generates dashboard and insights

Step 3: PDF Report

bash
Copy
Edit
python scripts/complete_pdf_generator.py
Creates a professional PDF report

📈 Analysis Components
Sentiment Analysis
Positive / Negative / Neutral classification

Emotional tone trends

Hashtag Analysis
Top job hashtags

Trending topics

Engagement Analytics
Likes, Retweets, Replies

User interaction metrics

Temporal Patterns
Peak hours and days

Optimal posting times

User Behavior
Most active users

Influencer detection

📊 Sample Outputs
Pie Chart: Sentiment Distribution

Bar Charts: Top Hashtags, Keywords, Active Users

Histograms: Tweet Length, Sentiment Score

Line/Scatter Plots: Tweet Activity, Engagement vs Views

PDF Report: With all charts embedded

📋 Data Schema
Column	Type	Description
Username	String	Twitter handle
Tweet	String	Tweet content
Date	Date	Posting date
Time	Time	Posting time
Mentions	String	Mentioned users
Hashtags	String	Used hashtags
Likes	Integer	Like count
Retweets	Integer	Retweet count
Replies	Integer	Reply count
Views	Integer	View count

🎯 Use Cases
📊 Job Market Research

🧠 Social Media Strategy

🕵️‍♀️ Recruitment Intelligence

📈 Industry Trend Analysis

🎓 Academic Studies

⚙️ Configuration
Inside twitter_scraper.py:

python
Copy
Edit
job_hashtags = ["naukri", "jobs", "jobseeker", "vacancy"]
max_tweets = 2000
headless_mode = False
Inside analysis scripts:

python
Copy
Edit
figure_size = (20, 24)
dpi = 300
🔍 Sample Analysis Results
2000+ tweets analyzed from 400+ users

Sentiment and engagement trends visualized

Best time to post identified

Fully formatted PDF reports

yaml
Copy
Edit
