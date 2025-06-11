import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import itertools
import re
from textblob import TextBlob
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# PDF generation imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os

class TwitterJobAnalysisFullPDFReport:
    def __init__(self, csv_file='twitter_job_analysis.csv'):
        self.csv_file = csv_file
        self.df = None
        self.load_and_prepare_data()
        
    def load_and_prepare_data(self):
        """Load and prepare the CSV data"""
        try:
            self.df = pd.read_csv(self.csv_file)
            print(f"✅ Successfully loaded {len(self.df)} tweets from {self.csv_file}")
            
            # Handle datetime parsing
            try:
                self.df['datetime'] = pd.to_datetime(self.df['Date'] + ' ' + self.df['Time'], errors='coerce')
            except:
                clean_time = self.df['Time'].str.replace(r'\.\d+', '', regex=True)
                self.df['datetime'] = pd.to_datetime(self.df['Date'] + ' ' + clean_time, errors='coerce')
            
            # Parse hashtags and mentions
            self.df['hashtags_list'] = self.df['Hashtags'].apply(self.parse_list)
            self.df['mentions_list'] = self.df['Mentions'].apply(self.parse_list)
            
            # Ensure numeric columns
            for col in ['Likes', 'Retweets', 'Replies', 'Views']:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
            
            # Calculate engagement metrics
            self.df['total_engagement'] = self.df['Likes'] + self.df['Retweets'] + self.df['Replies']
            self.df['engagement_rate'] = np.where(
                self.df['Views'] > 0, 
                (self.df['total_engagement'] / self.df['Views']) * 100, 
                0
            )
            
            # Add time features
            self.df['hour'] = self.df['datetime'].dt.hour
            self.df['day_of_week'] = self.df['datetime'].dt.day_name()
            
            print(f"📊 Data prepared: {len(self.df)} tweets from {self.df['Username'].nunique()} users")
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None
    
    def parse_list(self, text):
        """Parse comma-separated string to list"""
        if pd.isna(text) or text == '' or str(text).lower() == 'nan':
            return []
        return [item.strip() for item in str(text).split(',') if item.strip()]
    
    def perform_sentiment_analysis(self):
        """Perform sentiment analysis on tweets"""
        def get_sentiment(text):
            try:
                return TextBlob(str(text)).sentiment.polarity
            except:
                return 0
        
        def classify_sentiment(score):
            if score > 0.1:
                return 'Positive'
            elif score < -0.1:
                return 'Negative'
            else:
                return 'Neutral'
        
        self.df['sentiment_score'] = self.df['Tweet'].apply(get_sentiment)
        self.df['sentiment_label'] = self.df['sentiment_score'].apply(classify_sentiment)
        
        return self.df['sentiment_label'].value_counts()
    
    def analyze_hashtags(self):
        """Analyze hashtag usage"""
        all_hashtags = list(itertools.chain(*self.df['hashtags_list']))
        return Counter(all_hashtags).most_common(15)
    
    def analyze_keywords(self):
        """Extract and analyze keywords"""
        def extract_keywords(text):
            text = re.sub(r'http\S+|www\S+|https\S+', '', str(text), flags=re.MULTILINE)
            text = re.sub(r'@\w+|#\w+', '', text)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            stopwords = {'the', 'and', 'for', 'are', 'with', 'this', 'that', 'you', 'your', 
                        'our', 'can', 'will', 'have', 'has', 'been', 'from', 'they', 'them',
                        'job', 'jobs', 'work', 'career', 'hiring', 'vacancy', 'naukri'}
            return [word for word in words if word not in stopwords and len(word) > 2]
        
        all_words = list(itertools.chain(*self.df['Tweet'].apply(extract_keywords)))
        return Counter(all_words).most_common(20)
    
    def analyze_engagement(self):
        """Analyze engagement patterns"""
        stats = {
            'total_tweets': len(self.df),
            'unique_users': self.df['Username'].nunique(),
            'total_likes': int(self.df['Likes'].sum()),
            'total_retweets': int(self.df['Retweets'].sum()),
            'total_replies': int(self.df['Replies'].sum()),
            'total_views': int(self.df['Views'].sum()),
            'avg_likes': float(self.df['Likes'].mean()),
            'avg_retweets': float(self.df['Retweets'].mean()),
            'avg_replies': float(self.df['Replies'].mean()),
            'avg_views': float(self.df['Views'].mean()),
            'avg_engagement': float(self.df['total_engagement'].mean()),
            'max_engagement': int(self.df['total_engagement'].max())
        }
        
        return stats
    
    def analyze_temporal_patterns(self):
        """Analyze temporal patterns"""
        hourly_activity = self.df['hour'].value_counts().sort_index()
        daily_activity = self.df['day_of_week'].value_counts()
        user_activity = self.df['Username'].value_counts().head(10)
        
        return {
            'hourly': hourly_activity,
            'daily': daily_activity,
            'users': user_activity,
            'peak_hour': int(hourly_activity.idxmax()) if not hourly_activity.empty else 12,
            'peak_day': str(daily_activity.idxmax()) if not daily_activity.empty else 'Monday'
        }
    
    def create_all_12_charts(self):
        """Create all 12 individual charts for PDF inclusion"""
        print("📊 Creating all 12 charts for PDF inclusion...")
        
        # Perform all analyses
        sentiment_dist = self.perform_sentiment_analysis()
        hashtag_counts = self.analyze_hashtags()
        keyword_counts = self.analyze_keywords()
        engagement_stats = self.analyze_engagement()
        temporal_data = self.analyze_temporal_patterns()
        
        chart_files = []
        chart_titles = []
        
        # 1. Sentiment Distribution Pie Chart
        plt.figure(figsize=(8, 6))
        colors = ['#2E8B57', '#FF6B6B', '#4ECDC4']
        sentiment_dist.plot.pie(autopct='%1.1f%%', startangle=90, colors=colors)
        plt.title('Sentiment Distribution', fontsize=16, fontweight='bold')
        plt.ylabel('')
        plt.tight_layout()
        chart1 = 'chart1_sentiment_distribution.png'
        plt.savefig(chart1, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(chart1)
        chart_titles.append('Sentiment Distribution')
        
        # 2. Top 10 Hashtags Bar Chart
        plt.figure(figsize=(10, 6))
        if hashtag_counts:
            tags, counts = zip(*hashtag_counts[:10])
            plt.barh(range(len(tags)), counts, color='skyblue')
            plt.yticks(range(len(tags)), tags)
            plt.title('Top 10 Hashtags', fontsize=16, fontweight='bold')
            plt.xlabel('Count')
            plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        chart2 = 'chart2_top_hashtags.png'
        plt.savefig(chart2, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(chart2)
        chart_titles.append('Top 10 Hashtags')
        
        # 3. Top 10 Keywords Bar Chart
        plt.figure(figsize=(10, 6))
        if keyword_counts:
            words, counts = zip(*keyword_counts[:10])
            plt.barh(range(len(words)), counts, color='lightcoral')
            plt.yticks(range(len(words)), words)
            plt.title('Top 10 Keywords', fontsize=16, fontweight='bold')
            plt.xlabel('Count')
            plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        chart3 = 'chart3_top_keywords.png'
        plt.savefig(chart3, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(chart3)
        chart_titles.append('Top 10 Keywords')
        
        # 4. Average Engagement Metrics Bar Chart
        plt.figure(figsize=(8, 6))
        metrics = ['Likes', 'Retweets', 'Replies', 'Views']
        values = [engagement_stats['avg_likes'], engagement_stats['avg_retweets'], 
                 engagement_stats['avg_replies'], engagement_stats['avg_views']]
        bars = plt.bar(metrics, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'])
        plt.title('Average Engagement Metrics', fontsize=16, fontweight='bold')
        plt.ylabel('Average Count')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01, 
                    f'{value:.1f}', ha='center', va='bottom')
        plt.tight_layout()
        chart4 = 'chart4_engagement_metrics.png'
        plt.savefig(chart4, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(chart4)
        chart_titles.append('Average Engagement Metrics')
        
        # 5. Hourly Activity Line Chart
        plt.figure(figsize=(10, 6))
        temporal_data['hourly'].plot(kind='line', marker='o', linewidth=2, color='#2E8B57')
        plt.title('Tweet Activity by Hour', fontsize=16, fontweight='bold')
        plt.xlabel('Hour of Day')
        plt.ylabel('Tweet Count')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        chart5 = 'chart5_hourly_activity.png'
        plt.savefig(chart5, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(chart5)
        chart_titles.append('Tweet Activity by Hour')
        
        # 6. Daily Activity Bar Chart
        plt.figure(figsize=(8, 6))
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_reordered = temporal_data['daily'].reindex(day_order, fill_value=0)
        bars = plt.bar(range(len(daily_reordered)), daily_reordered.values, color='lightgreen')
        plt.xticks(range(len(daily_reordered)), [day[:3] for day in daily_reordered.index])
        plt.title('Tweet Activity by Day of Week', fontsize=16, fontweight='bold')
        plt.ylabel('Tweet Count')
        
        # Add value labels on bars
        for bar, value in zip(bars, daily_reordered.values):
            if value > 0:
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                        f'{value}', ha='center', va='bottom')
        plt.tight_layout()
        chart6 = 'chart6_daily_activity.png'
        plt.savefig(chart6, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(chart6)
        chart_titles.append('Tweet Activity by Day of Week')
        
        # 7. Top 10 Most Active Users
        plt.figure(figsize=(10, 6))
        plt.barh(range(len(temporal_data['users'])), temporal_data['users'].values, color='purple')
        plt.yticks(range(len(temporal_data['users'])), 
                  [f"{user[:12]}..." if len(user) > 12 else user for user in temporal_data['users'].index])
        plt.title('Top 10 Most Active Users', fontsize=16, fontweight='bold')
        plt.xlabel('Tweet Count')
        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        chart7 = 'chart7_active_users.png'
        plt.savefig(chart7, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(chart7)
        chart_titles.append('Top 10 Most Active Users')
        
        # 8. Engagement Rate Distribution
        plt.figure(figsize=(8, 6))
        plt.hist(self.df['engagement_rate'], bins=20, alpha=0.7, color='orange', edgecolor='black')
        plt.title('Engagement Rate Distribution', fontsize=16, fontweight='bold')
        plt.xlabel('Engagement Rate (%)')
        plt.ylabel('Frequency')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        chart8 = 'chart8_engagement_rate_dist.png'
        plt.savefig(chart8, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(chart8)
        chart_titles.append('Engagement Rate Distribution')
        
        # 9. Sentiment Score Distribution
        plt.figure(figsize=(8, 6))
        plt.hist(self.df['sentiment_score'], bins=20, alpha=0.7, color='cyan', edgecolor='black')
        plt.title('Sentiment Score Distribution', fontsize=16, fontweight='bold')
        plt.xlabel('Sentiment Score')
        plt.ylabel('Frequency')
        plt.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='Neutral')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        chart9 = 'chart9_sentiment_score_dist.png'
        plt.savefig(chart9, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(chart9)
        chart_titles.append('Sentiment Score Distribution')
        
        # 10. Tweet Length Distribution
        plt.figure(figsize=(8, 6))
        tweet_lengths = self.df['Tweet'].str.len()
        plt.hist(tweet_lengths, bins=20, alpha=0.7, color='gold', edgecolor='black')
        plt.title('Tweet Length Distribution', fontsize=16, fontweight='bold')
        plt.xlabel('Tweet Length (characters)')
        plt.ylabel('Frequency')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        chart10 = 'chart10_tweet_length_dist.png'
        plt.savefig(chart10, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(chart10)
        chart_titles.append('Tweet Length Distribution')
        
        # 11. Engagement vs Views Scatter Plot
        plt.figure(figsize=(8, 6))
        plt.scatter(self.df['Views'], self.df['total_engagement'], alpha=0.6, color='navy')
        plt.xlabel('Views')
        plt.ylabel('Total Engagement')
        plt.title('Engagement vs Views Correlation', fontsize=16, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        chart11 = 'chart11_engagement_vs_views.png'
        plt.savefig(chart11, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(chart11)
        chart_titles.append('Engagement vs Views Correlation')
        
        # 12. Top 5 Most Engaging Tweets
        plt.figure(figsize=(10, 6))
        top_5_tweets = self.df.nlargest(5, 'total_engagement')
        plt.barh(range(len(top_5_tweets)), top_5_tweets['total_engagement'], color='gold')
        plt.yticks(range(len(top_5_tweets)), 
                  [f"@{user[:10]}..." for user in top_5_tweets['Username']])
        plt.title('Top 5 Most Engaging Tweets', fontsize=16, fontweight='bold')
        plt.xlabel('Total Engagement')
        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        chart12 = 'chart12_top_engaging_tweets.png'
        plt.savefig(chart12, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(chart12)
        chart_titles.append('Top 5 Most Engaging Tweets')
        
        return chart_files, chart_titles, sentiment_dist, hashtag_counts, keyword_counts, engagement_stats, temporal_data
    
    def generate_full_pdf_report(self):
        """Generate comprehensive PDF report with all 12 embedded charts"""
        print("📄 Generating comprehensive PDF report with all 12 visualizations...")
        
        # Create all charts and get analysis data
        chart_files, chart_titles, sentiment_dist, hashtag_counts, keyword_counts, engagement_stats, temporal_data = self.create_all_12_charts()
        
        # Create PDF document
        pdf_filename = 'Twitter_Job_Analysis_Complete_Report.pdf'
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter, topMargin=0.5*inch)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        )
        
        chart_title_style = ParagraphStyle(
            'ChartTitle',
            parent=styles['Heading3'],
            fontSize=14,
            spaceAfter=6,
            spaceBefore=12,
            alignment=TA_CENTER,
            textColor=colors.darkgreen
        )
        
        # Build PDF content
        content = []
        
        # Title Page
        content.append(Paragraph("COMPREHENSIVE TWITTER JOB DATA ANALYSIS REPORT", title_style))
        content.append(Spacer(1, 0.3*inch))
        content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        content.append(Paragraph(f"Data Source: {self.csv_file}", styles['Normal']))
        content.append(Spacer(1, 0.5*inch))
        
        # Executive Summary
        content.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
        summary_text = f"""
        This comprehensive analysis examines {engagement_stats['total_tweets']} Twitter tweets 
        related to job searches, career opportunities, and employment discussions collected 
        from {engagement_stats['unique_users']} unique users.
        
        <b>Key Metrics Overview:</b><br/>
        • Total Tweets Analyzed: {engagement_stats['total_tweets']}<br/>
        • Unique Users: {engagement_stats['unique_users']}<br/>
        • Date Range: {self.df['Date'].min()} to {self.df['Date'].max()}<br/>
        • Total Engagement: {engagement_stats['total_likes'] + engagement_stats['total_retweets'] + engagement_stats['total_replies']}<br/>
        • Total Views: {engagement_stats['total_views']}<br/>
        • Average Engagement per Tweet: {engagement_stats['avg_engagement']:.2f}
        """
        content.append(Paragraph(summary_text, styles['Normal']))
        content.append(PageBreak())
        
        # Add all 12 charts with descriptions
        chart_descriptions = [
            f"This pie chart shows the distribution of sentiment across all {engagement_stats['total_tweets']} tweets. {sentiment_dist.idxmax()} sentiment dominates the conversation.",
            f"The top 10 hashtags reveal the most popular tags used in job-related discussions. {hashtag_counts[0][0]} is the most frequently used hashtag.",
            f"Key terms and phrases that appear most frequently in tweets, excluding common stopwords and job-related terms.",
            f"Average engagement metrics showing the typical performance across likes, retweets, replies, and views per tweet.",
            f"Hourly activity pattern showing peak tweet activity at {temporal_data['peak_hour']}:00, indicating optimal posting times.",
            f"Weekly activity distribution showing {temporal_data['peak_day']} as the most active day for job-related discussions.",
            f"The most active users in the dataset, showing community leaders and frequent contributors to job discussions.",
            f"Distribution of engagement rates across all tweets, showing how effectively content converts views into interactions.",
            f"Sentiment score distribution showing the emotional tone of job-related conversations on a scale from -1 (negative) to +1 (positive).",
            f"Character length distribution of tweets, showing optimal tweet length patterns for job-related content.",
            f"Correlation between total views and engagement, indicating how visibility translates to user interactions.",
            f"The highest-performing tweets by total engagement, showcasing content that resonates most with the audience."
        ]
        
        for i, (chart_file, chart_title, description) in enumerate(zip(chart_files, chart_titles, chart_descriptions), 1):
            content.append(Paragraph(f"Chart {i}: {chart_title}", chart_title_style))
            
            if os.path.exists(chart_file):
                # Adjust image size based on chart type
                if i in [2, 3, 7]:  # Horizontal bar charts need more width
                    img = Image(chart_file, width=7*inch, height=4.2*inch)
                else:
                    img = Image(chart_file, width=6*inch, height=4.5*inch)
                content.append(img)
            
            content.append(Spacer(1, 0.1*inch))
            content.append(Paragraph(description, styles['Normal']))
            content.append(Spacer(1, 0.2*inch))
            
            # Add page break after every 2 charts except the last one
            if i % 2 == 0 and i < len(chart_files):
                content.append(PageBreak())
        
        # Analysis Summary Page
        content.append(PageBreak())
        content.append(Paragraph("DETAILED ANALYSIS SUMMARY", heading_style))
        
        # Sentiment Analysis Summary
        content.append(Paragraph("Sentiment Analysis", chart_title_style))
        sentiment_text = f"""
        <b>Sentiment Distribution:</b><br/>
        """
        for sentiment, count in sentiment_dist.items():
            percentage = (count / len(self.df)) * 100
            sentiment_text += f"• {sentiment}: {count} tweets ({percentage:.1f}%)<br/>"
        
        sentiment_text += f"""<br/>
        <b>Average Sentiment Score:</b> {self.df['sentiment_score'].mean():.3f}<br/>
        The overall sentiment is {sentiment_dist.idxmax().lower()}, indicating a {sentiment_dist.idxmax().lower()} tone in job-related discussions.
        """
        content.append(Paragraph(sentiment_text, styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        # Hashtag Analysis Summary
        content.append(Paragraph("Hashtag Analysis", chart_title_style))
        hashtag_text = f"""
        <b>Top 5 Hashtags:</b><br/>
        """
        for i, (hashtag, count) in enumerate(hashtag_counts[:5], 1):
            hashtag_text += f"{i}. {hashtag}: {count} occurrences<br/>"
        
        total_hashtags = len(set(itertools.chain(*self.df['hashtags_list'])))
        hashtag_text += f"""<br/>
        <b>Total Unique Hashtags:</b> {total_hashtags}<br/>
        <b>Average Hashtags per Tweet:</b> {self.df['hashtags_list'].apply(len).mean():.2f}
        """
        content.append(Paragraph(hashtag_text, styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        # Engagement Summary
        content.append(Paragraph("Engagement Summary", chart_title_style))
        engagement_text = f"""
        <b>Total Engagement:</b> {engagement_stats['total_likes'] + engagement_stats['total_retweets'] + engagement_stats['total_replies']}<br/>
        <b>Average Engagement per Tweet:</b> {engagement_stats['avg_engagement']:.2f}<br/>
        <b>Highest Engagement:</b> {engagement_stats['max_engagement']} interactions<br/>
        <b>Peak Activity:</b> {temporal_data['peak_hour']}:00 on {temporal_data['peak_day']}s
        """
        content.append(Paragraph(engagement_text, styles['Normal']))
        
        # Recommendations Section
        content.append(PageBreak())
        content.append(Paragraph("ACTIONABLE RECOMMENDATIONS", heading_style))
        
        recommendations_text = f"""
        <b>1. Optimal Posting Strategy:</b><br/>
        • Post during peak hour: {temporal_data['peak_hour']}:00 for maximum visibility<br/>
        • Focus on {temporal_data['peak_day']}s for highest engagement<br/><br/>
        
        <b>2. Content Optimization:</b><br/>
        • Use top hashtags: {', '.join([tag for tag, _ in hashtag_counts[:3]])}<br/>
        • Focus on {sentiment_dist.idxmax().lower()} sentiment content<br/>
        • Target average engagement above {engagement_stats['avg_engagement']:.1f}<br/><br/>
        
        <b>3. Community Engagement:</b><br/>
        • Engage with top active users for amplification<br/>
        • Monitor sentiment trends for market insights<br/>
        • Maintain consistent posting during peak hours
        """
        content.append(Paragraph(recommendations_text, styles['Normal']))
        
        # Conclusion
        content.append(Spacer(1, 0.3*inch))
        content.append(Paragraph("CONCLUSION", heading_style))
        
        conclusion_text = f"""
        This comprehensive analysis of {engagement_stats['total_tweets']} job-related tweets provides 
        actionable insights for optimizing Twitter engagement in the professional networking space. 
        
        The analysis reveals a {sentiment_dist.idxmax().lower()} sentiment landscape with peak activity 
        at {temporal_data['peak_hour']}:00 on {temporal_data['peak_day']}s. Implementation of the 
        recommended strategies should result in improved engagement rates and expanded reach 
        within the job market community.
        
        For ongoing optimization, regular analysis updates are recommended to track performance 
        improvements and adapt to evolving market conditions.
        """
        content.append(Paragraph(conclusion_text, styles['Normal']))
        
        # Build PDF
        doc.build(content)
        
        # Clean up chart files
        for chart_file in chart_files:
            if os.path.exists(chart_file):
                os.remove(chart_file)
        
        print(f"\n✅ Complete PDF report with all 12 charts generated successfully!")
        print(f"📄 Report saved as: {pdf_filename}")
        print(f"\n📊 Report includes:")
        print(f"   • Executive summary with key metrics")
        print(f"   • All 12 individual charts with descriptions")
        print(f"   • Detailed analysis summary")
        print(f"   • Actionable recommendations")
        print(f"\n📋 Analysis Summary:")
        print(f"   • {engagement_stats['total_tweets']} tweets analyzed")
        print(f"   • {engagement_stats['unique_users']} unique users")
        print(f"   • {sentiment_dist.idxmax()} sentiment dominance")
        print(f"   • Peak activity: {temporal_data['peak_hour']}:00 on {temporal_data['peak_day']}s")
        
        return pdf_filename

# Execute the complete PDF report generation
def generate_complete_pdf_report():
    """Generate comprehensive PDF report with all 12 visualizations"""
    print("🚀 Starting Complete PDF Report Generation with All 12 Charts...")
    
    try:
        analyzer = TwitterJobAnalysisFullPDFReport('twitter_job_analysis.csv')
        
        if analyzer.df is None:
            print("❌ Failed to load data. Please ensure twitter_job_analysis.csv exists.")
            return None
        
        pdf_file = analyzer.generate_full_pdf_report()
        
        print("\n🎯 Complete PDF Report Generated!")
        print(f"📄 File: {pdf_file}")
        print("   ✅ Includes all 12 charts with individual descriptions")
        print("   ✅ Professional formatting with ReportLab")
        print("   ✅ Executive summary and detailed analysis")
        print("   ✅ Actionable recommendations")
        print("   ✅ Ready for presentation and sharing")
        
        return pdf_file
        
    except Exception as e:
        print(f"❌ Error during PDF generation: {e}")
        return None

# Run the complete PDF generation
if __name__ == "__main__":
    # Install required package first
    print("📦 Installing ReportLab for PDF generation...")
    import subprocess
    try:
        subprocess.check_call(['pip', 'install', 'reportlab'])
    except:
        print("Please install reportlab manually: pip install reportlab")
    
    pdf_report = generate_complete_pdf_report()
