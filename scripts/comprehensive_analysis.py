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

class TwitterJobAnalysisReport:
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
        
        top_tweets = self.df.nlargest(5, 'total_engagement')[
            ['Username', 'Tweet', 'total_engagement', 'Likes', 'Retweets', 'Replies']
        ]
        
        return stats, top_tweets
    
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
    
    def create_comprehensive_visualizations(self):
        """Create comprehensive visualization dashboard"""
        # Perform all analyses
        sentiment_dist = self.perform_sentiment_analysis()
        hashtag_counts = self.analyze_hashtags()
        keyword_counts = self.analyze_keywords()
        engagement_stats, top_tweets = self.analyze_engagement()
        temporal_data = self.analyze_temporal_patterns()
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 24))
        
        # 1. Sentiment Distribution
        plt.subplot(4, 3, 1)
        colors = ['#2E8B57', '#FF6B6B', '#4ECDC4']
        sentiment_dist.plot.pie(autopct='%1.1f%%', startangle=90, colors=colors)
        plt.title('Sentiment Distribution', fontsize=14, fontweight='bold')
        plt.ylabel('')
        
        # 2. Top Hashtags
        plt.subplot(4, 3, 2)
        if hashtag_counts:
            tags, counts = zip(*hashtag_counts[:10])
            plt.barh(range(len(tags)), counts, color='skyblue')
            plt.yticks(range(len(tags)), tags)
            plt.title('Top 10 Hashtags', fontsize=14, fontweight='bold')
            plt.xlabel('Count')
        
        # 3. Top Keywords
        plt.subplot(4, 3, 3)
        if keyword_counts:
            words, counts = zip(*keyword_counts[:10])
            plt.barh(range(len(words)), counts, color='lightcoral')
            plt.yticks(range(len(words)), words)
            plt.title('Top 10 Keywords', fontsize=14, fontweight='bold')
            plt.xlabel('Count')
        
        # 4. Engagement Metrics
        plt.subplot(4, 3, 4)
        metrics = ['Likes', 'Retweets', 'Replies', 'Views']
        values = [engagement_stats['avg_likes'], engagement_stats['avg_retweets'], 
                 engagement_stats['avg_replies'], engagement_stats['avg_views']]
        bars = plt.bar(metrics, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'])
        plt.title('Average Engagement Metrics', fontsize=14, fontweight='bold')
        plt.ylabel('Average Count')
        plt.xticks(rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01, 
                    f'{value:.1f}', ha='center', va='bottom')
        
        # 5. Hourly Activity
        plt.subplot(4, 3, 5)
        temporal_data['hourly'].plot(kind='line', marker='o', linewidth=2, color='#2E8B57')
        plt.title('Tweet Activity by Hour', fontsize=14, fontweight='bold')
        plt.xlabel('Hour of Day')
        plt.ylabel('Tweet Count')
        plt.grid(True, alpha=0.3)
        
        # 6. Daily Activity
        plt.subplot(4, 3, 6)
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_reordered = temporal_data['daily'].reindex(day_order, fill_value=0)
        bars = plt.bar(range(len(daily_reordered)), daily_reordered.values, color='lightgreen')
        plt.xticks(range(len(daily_reordered)), [day[:3] for day in daily_reordered.index])
        plt.title('Tweet Activity by Day of Week', fontsize=14, fontweight='bold')
        plt.ylabel('Tweet Count')
        
        # 7. Top Active Users
        plt.subplot(4, 3, 7)
        plt.barh(range(len(temporal_data['users'])), temporal_data['users'].values, color='purple')
        plt.yticks(range(len(temporal_data['users'])), 
                  [f"{user[:12]}..." if len(user) > 12 else user for user in temporal_data['users'].index])
        plt.title('Top 10 Most Active Users', fontsize=14, fontweight='bold')
        plt.xlabel('Tweet Count')
        
        # 8. Engagement Rate Distribution
        plt.subplot(4, 3, 8)
        plt.hist(self.df['engagement_rate'], bins=20, alpha=0.7, color='orange', edgecolor='black')
        plt.title('Engagement Rate Distribution', fontsize=14, fontweight='bold')
        plt.xlabel('Engagement Rate (%)')
        plt.ylabel('Frequency')
        
        # 9. Sentiment Score Distribution
        plt.subplot(4, 3, 9)
        plt.hist(self.df['sentiment_score'], bins=20, alpha=0.7, color='cyan', edgecolor='black')
        plt.title('Sentiment Score Distribution', fontsize=14, fontweight='bold')
        plt.xlabel('Sentiment Score')
        plt.ylabel('Frequency')
        plt.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='Neutral')
        plt.legend()
        
        # 10. Tweet Length Distribution
        plt.subplot(4, 3, 10)
        tweet_lengths = self.df['Tweet'].str.len()
        plt.hist(tweet_lengths, bins=20, alpha=0.7, color='gold', edgecolor='black')
        plt.title('Tweet Length Distribution', fontsize=14, fontweight='bold')
        plt.xlabel('Tweet Length (characters)')
        plt.ylabel('Frequency')
        
        # 11. Engagement vs Views Scatter
        plt.subplot(4, 3, 11)
        plt.scatter(self.df['Views'], self.df['total_engagement'], alpha=0.6, color='navy')
        plt.xlabel('Views')
        plt.ylabel('Total Engagement')
        plt.title('Engagement vs Views', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        
        # 12. Top Tweets by Engagement
        plt.subplot(4, 3, 12)
        top_5_tweets = self.df.nlargest(5, 'total_engagement')
        plt.barh(range(len(top_5_tweets)), top_5_tweets['total_engagement'], color='gold')
        plt.yticks(range(len(top_5_tweets)), 
                  [f"@{user[:10]}..." for user in top_5_tweets['Username']])
        plt.title('Top 5 Most Engaging Tweets', fontsize=14, fontweight='bold')
        plt.xlabel('Total Engagement')
        
        plt.tight_layout(pad=3.0)
        plt.savefig('comprehensive_twitter_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        return sentiment_dist, hashtag_counts, keyword_counts, engagement_stats, top_tweets, temporal_data
    
    def generate_comprehensive_report(self):
        """Generate comprehensive PDF-style report"""
        print("🚀 Generating comprehensive Twitter job data analysis report...")
        
        # Create visualizations and get analysis data
        sentiment_dist, hashtag_counts, keyword_counts, engagement_stats, top_tweets, temporal_data = self.create_comprehensive_visualizations()
        
        # Generate comprehensive text report
        report_content = f"""
{'='*80}
COMPREHENSIVE TWITTER JOB DATA ANALYSIS REPORT
{'='*80}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Source: {self.csv_file}
Visualization: comprehensive_twitter_analysis.png

{'='*80}
EXECUTIVE SUMMARY
{'='*80}

This comprehensive analysis examines {engagement_stats['total_tweets']} Twitter tweets 
related to job searches, career opportunities, and employment discussions collected 
from {engagement_stats['unique_users']} unique users.

Key Metrics Overview:
• Total Tweets Analyzed: {engagement_stats['total_tweets']}
• Unique Users: {engagement_stats['unique_users']}
• Date Range: {self.df['Date'].min()} to {self.df['Date'].max()}
• Total Engagement: {engagement_stats['total_likes'] + engagement_stats['total_retweets'] + engagement_stats['total_replies']}
• Total Views: {engagement_stats['total_views']}
• Average Engagement per Tweet: {engagement_stats['avg_engagement']:.2f}

{'='*80}
1. SENTIMENT ANALYSIS INSIGHTS
{'='*80}

Sentiment Distribution:
"""
        
        for sentiment, count in sentiment_dist.items():
            percentage = (count / len(self.df)) * 100
            report_content += f"• {sentiment}: {count} tweets ({percentage:.1f}%)\n"
        
        report_content += f"""
Average Sentiment Score: {self.df['sentiment_score'].mean():.3f}
(Scale: -1.0 = Very Negative, 0.0 = Neutral, +1.0 = Very Positive)

Key Findings:
• The overall sentiment is {sentiment_dist.idxmax().lower()}, indicating a {sentiment_dist.idxmax().lower()} tone in job-related discussions
• Sentiment analysis reveals the emotional landscape of job seekers and employers
• {sentiment_dist.idxmax()} sentiment dominates with {sentiment_dist.max()} tweets

{'='*80}
2. HASHTAG ANALYSIS & TRENDING TOPICS
{'='*80}

Top 15 Most Popular Hashtags:
"""
        
        for i, (hashtag, count) in enumerate(hashtag_counts[:15], 1):
            report_content += f"{i:2d}. {hashtag}: {count} occurrences\n"
        
        total_hashtags = len(set(itertools.chain(*self.df['hashtags_list'])))
        avg_hashtags = self.df['hashtags_list'].apply(len).mean()
        
        report_content += f"""
Hashtag Statistics:
• Total Unique Hashtags: {total_hashtags}
• Average Hashtags per Tweet: {avg_hashtags:.2f}
• Most Popular Hashtag: {hashtag_counts[0][0]} ({hashtag_counts[0][1]} uses)

{'='*80}
3. ENGAGEMENT ANALYSIS & PERFORMANCE METRICS
{'='*80}

Overall Engagement Statistics:
• Total Likes: {engagement_stats['total_likes']}
• Total Retweets: {engagement_stats['total_retweets']}
• Total Replies: {engagement_stats['total_replies']}
• Total Views: {engagement_stats['total_views']}

Average Engagement per Tweet:
• Average Likes: {engagement_stats['avg_likes']:.2f}
• Average Retweets: {engagement_stats['avg_retweets']:.2f}
• Average Replies: {engagement_stats['avg_replies']:.2f}
• Average Views: {engagement_stats['avg_views']:.2f}
• Average Total Engagement: {engagement_stats['avg_engagement']:.2f}


4. TEMPORAL ANALYSIS & ACTIVITY PATTERNS
{'='*80}

Peak Activity Patterns:
• Peak Hour: {temporal_data['peak_hour']}:00 ({temporal_data['hourly'][temporal_data['peak_hour']]} tweets)
• Most Active Day: {temporal_data['peak_day']} ({temporal_data['daily'][temporal_data['peak_day']]} tweets)

{'='*80}
5. ACTIONABLE RECOMMENDATIONS
{'='*80}

CONTENT OPTIMIZATION STRATEGIES:

1. Hashtag Strategy:
   • Use top-performing hashtags: {', '.join([tag for tag, _ in hashtag_counts[:5]])}
   • Combine popular hashtags with niche ones for broader reach

2. Timing Optimization:
   • Post during peak hour: {temporal_data['peak_hour']}:00 for maximum visibility
   • Focus on {temporal_data['peak_day']}s for highest engagement potential

3. Content Creation:
   • Focus on {sentiment_dist.idxmax().lower()} sentiment content for better engagement
   • Model content after top-performing tweets identified in analysis

{'='*80}
CONCLUSION
{'='*80}

This comprehensive analysis of {engagement_stats['total_tweets']} job-related tweets provides 
actionable insights for optimizing Twitter engagement in the professional networking space. 

The analysis reveals a {sentiment_dist.idxmax().lower()} sentiment landscape with peak activity 
at {temporal_data['peak_hour']}:00 on {temporal_data['peak_day']}s.

Report generated by Twitter Job Data Analyzer
Analysis completed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Visualization dashboard: comprehensive_twitter_analysis.png

{'='*80}
END OF REPORT
{'='*80}
"""
        
        # Save comprehensive report
        report_filename = 'Comprehensive_Twitter_Job_Analysis_Report.txt'
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n✅ Comprehensive analysis completed successfully!")
        print(f"📄 Report saved as: {report_filename}")
        print(f"📊 Visualization saved as: comprehensive_twitter_analysis.png")
        print(f"\n📋 Analysis Summary:")
        print(f"   • {engagement_stats['total_tweets']} tweets analyzed")
        print(f"   • {engagement_stats['unique_users']} unique users")
        print(f"   • {sentiment_dist.idxmax()} sentiment dominance")
        print(f"   • Peak activity: {temporal_data['peak_hour']}:00 on {temporal_data['peak_day']}s")
        
        return report_content

# Execute the comprehensive analysis
def run_comprehensive_analysis():
    """Run the complete Twitter job data analysis"""
    print("🚀 Starting Comprehensive Twitter Job Data Analysis...")
    
    try:
        analyzer = TwitterJobAnalysisReport('twitter_job_analysis.csv')
        
        if analyzer.df is None:
            print("❌ Failed to load data. Please ensure twitter_job_analysis.csv exists.")
            return None
        
        report = analyzer.generate_comprehensive_report()
        
        print("\n🎯 Analysis Complete! Files Generated:")
        print("   📊 comprehensive_twitter_analysis.png (12-panel visualization dashboard)")
        print("   📄 Comprehensive_Twitter_Job_Analysis_Report.txt (detailed analysis report)")
        
        return report
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return None

# Run the analysis
if __name__ == "__main__":
    report = run_comprehensive_analysis()
