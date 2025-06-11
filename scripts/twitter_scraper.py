import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import re
import json
from tqdm import tqdm

def save_to_csv(tweets_data, filename='twitter_job_data.csv'):
    """
    Save tweets data to CSV with specified column format
    """
    if not tweets_data:
        print("No data to save!")
        return None
    
    # Prepare data for CSV with specified columns
    data_for_csv = []
    
    for tweet in tweets_data:
        # Extract date and time separately from ISO datetime
        date_time = tweet.get('date_time', '')
        date = ''
        time = ''
        
        if date_time:
            try:
                # Parse the datetime string
                if 'T' in date_time:
                    dt_obj = pd.to_datetime(date_time)
                else:
                    dt_obj = pd.to_datetime(date_time)
                
                date = dt_obj.date().isoformat()
                time = dt_obj.time().isoformat()
            except Exception as e:
                # Fallback to current date/time if parsing fails
                now = datetime.now()
                date = now.date().isoformat()
                time = now.time().isoformat()
        
        # Format mentions and hashtags as comma-separated strings
        mentions_str = ','.join(tweet.get('mentions', []))
        hashtags_str = ','.join(tweet.get('hashtags', []))
        
        data_for_csv.append({
            'Username': tweet.get('username', ''),
            'Tweet': tweet.get('tweet', ''),
            'Date': date,
            'Time': time,
            'Mentions': mentions_str,
            'Hashtags': hashtags_str,
            'Likes': tweet.get('likes', 0),
            'Retweets': tweet.get('retweets', 0),
            'Comments': tweet.get('comments', 0),
            'Replies': tweet.get('replies', 0),
            'Views': tweet.get('views', 0)
        })
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(data_for_csv)
    df.to_csv(filename, index=False, encoding='utf-8')
    
    print(f"\n✅ CSV file '{filename}' generated successfully!")
    print(f"📊 Total records saved: {len(df)}")
    print(f"📁 File location: {filename}")
    
    # Display preview of the data
    print(f"\n📋 Preview of saved data:")
    print(df.head().to_string(index=False))
    
    return df

class TwitterScraper:
    def __init__(self, headless=False):
        """Initialize the Twitter scraper with Chrome driver"""
        self.driver = None
        self.tweets_data = []
        self.setup_driver(headless)
    
    def setup_driver(self, headless=False):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def search_hashtags(self, hashtags, max_tweets=2000):
        """Search for tweets containing specified hashtags"""
        # Create search query for multiple hashtags
        search_query = " OR ".join([f"#{tag}" for tag in hashtags])
        encoded_query = search_query.replace(" ", "%20").replace("#", "%23")
        
        # Navigate to Twitter search page
        search_url = f"https://twitter.com/search?q={encoded_query}&src=typed_query&f=live"
        print(f"🔍 Searching for: {search_query}")
        
        self.driver.get(search_url)
        time.sleep(5)
        
        # Handle potential login prompts or rate limiting
        self.handle_initial_page()
        
        # Scroll and collect tweets
        self.infinite_scroll_and_scrape(max_tweets)
    
    def handle_initial_page(self):
        """Handle initial page load and potential prompts"""
        try:
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweet"]'))
            )
        except:
            print("⚠️ Initial page load timeout - continuing anyway")
            time.sleep(3)
    
    def infinite_scroll_and_scrape(self, max_tweets):
        """Implement infinite scrolling to load more tweets"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        tweets_collected = 0
        scroll_attempts = 0
        max_scroll_attempts = 100  # Increased for 2000 tweets
        
        print(f"🚀 Starting to collect up to {max_tweets} tweets...")
        
        while tweets_collected < max_tweets and scroll_attempts < max_scroll_attempts:
            # Extract tweets from current view
            current_tweets = self.extract_tweets_from_page()
            new_tweets = 0
            
            for tweet_data in current_tweets:
                if tweet_data and not self.is_duplicate_tweet(tweet_data):
                    self.tweets_data.append(tweet_data)
                    tweets_collected += 1
                    new_tweets += 1
                    
                    if tweets_collected >= max_tweets:
                        break
            
            print(f"📝 Collected {new_tweets} new tweets. Total: {tweets_collected}/{max_tweets}")
            
            # Scroll down to load more tweets
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Check if new content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
                time.sleep(2)
            else:
                scroll_attempts = 0
                last_height = new_height
    
    def is_duplicate_tweet(self, new_tweet):
        """Check if tweet is already collected"""
        for existing_tweet in self.tweets_data:
            if (existing_tweet.get('username') == new_tweet.get('username') and 
                existing_tweet.get('tweet') == new_tweet.get('tweet')):
                return True
        return False
    
    def extract_tweets_from_page(self):
        """Extract tweet data from the current page"""
        tweets = []
        
        try:
            # Find all tweet containers
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
            
            for tweet_element in tweet_elements:
                try:
                    tweet_data = self.extract_single_tweet(tweet_element)
                    if tweet_data:
                        tweets.append(tweet_data)
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"❌ Error extracting tweets: {e}")
        
        return tweets
    
    def extract_single_tweet(self, tweet_element):
        """Extract data from a single tweet element"""
        try:
            tweet_data = {}
            
            # Extract username
            try:
                username_elements = tweet_element.find_elements(By.CSS_SELECTOR, '[data-testid="User-Name"] span')
                for elem in username_elements:
                    text = elem.text
                    if text.startswith('@'):
                        tweet_data['username'] = text.replace('@', '')
                        break
                else:
                    # Fallback method
                    username_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"] a')
                    href = username_element.get_attribute('href')
                    if href:
                        tweet_data['username'] = href.split('/')[-1]
            except:
                tweet_data['username'] = "Unknown"
            
            # Extract tweet text
            try:
                tweet_text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                tweet_data['tweet'] = tweet_text_element.text
            except:
                tweet_data['tweet'] = ""
            
            # Skip if no tweet content
            if not tweet_data['tweet']:
                return None
            
            # Extract date and time
            try:
                time_element = tweet_element.find_element(By.CSS_SELECTOR, 'time')
                tweet_data['date_time'] = time_element.get_attribute('datetime')
            except:
                tweet_data['date_time'] = datetime.now().isoformat()
            
            # Extract hashtags from tweet text
            hashtags = re.findall(r'#\w+', tweet_data['tweet'])
            tweet_data['hashtags'] = hashtags
            
            # Extract mentions from tweet text
            mentions = re.findall(r'@\w+', tweet_data['tweet'])
            tweet_data['mentions'] = [mention.replace('@', '') for mention in mentions]
            
            # Extract engagement metrics
            tweet_data.update(self.extract_engagement_metrics(tweet_element))
            
            return tweet_data
            
        except Exception as e:
            return None
    
    def extract_engagement_metrics(self, tweet_element):
        """Extract likes, retweets, comments, replies, and views"""
        metrics = {
            'likes': 0,
            'retweets': 0,
            'comments': 0,
            'replies': 0,
            'views': 0
        }
        
        try:
            # Extract likes
            try:
                likes_button = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="like"]')
                likes_text = likes_button.get_attribute('aria-label') or ''
                if 'like' in likes_text.lower():
                    numbers = re.findall(r'\d+', likes_text)
                    if numbers:
                        metrics['likes'] = int(numbers[0])
            except:
                pass
            
            # Extract retweets
            try:
                retweet_button = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="retweet"]')
                retweet_text = retweet_button.get_attribute('aria-label') or ''
                if 'retweet' in retweet_text.lower():
                    numbers = re.findall(r'\d+', retweet_text)
                    if numbers:
                        metrics['retweets'] = int(numbers[0])
            except:
                pass
            
            # Extract replies
            try:
                reply_button = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="reply"]')
                reply_text = reply_button.get_attribute('aria-label') or ''
                if 'repl' in reply_text.lower():
                    numbers = re.findall(r'\d+', reply_text)
                    if numbers:
                        metrics['replies'] = int(numbers[0])
                        metrics['comments'] = metrics['replies']  # Twitter uses replies as comments
            except:
                pass
            
            # Extract views (alternative methods)
            try:
                # Method 1: Look for analytics link
                analytics_link = tweet_element.find_element(By.CSS_SELECTOR, '[href*="analytics"]')
                if analytics_link:
                    aria_label = analytics_link.get_attribute('aria-label') or ''
                    numbers = re.findall(r'[\d,]+', aria_label)
                    if numbers:
                        views_str = numbers[0].replace(',', '')
                        metrics['views'] = int(views_str)
            except:
                # Method 2: Look for view count in various elements
                try:
                    view_elements = tweet_element.find_elements(By.CSS_SELECTOR, '[role="group"] span, [role="button"] span')
                    for element in view_elements:
                        text = element.text
                        if any(indicator in text.lower() for indicator in ['view', 'k', 'm']) and any(char.isdigit() for char in text):
                            metrics['views'] = self.parse_metric_count(text)
                            break
                except:
                    pass
                
        except Exception as e:
            pass
        
        return metrics
    
    def parse_metric_count(self, count_text):
        """Parse metric count text (e.g., '1.2K', '5M') to integer"""
        if not count_text or count_text == '':
            return 0
        
        try:
            count_text = count_text.strip().replace(',', '')
            
            if 'K' in count_text.upper():
                return int(float(count_text.upper().replace('K', '')) * 1000)
            elif 'M' in count_text.upper():
                return int(float(count_text.upper().replace('M', '')) * 1000000)
            else:
                # Extract numbers from text
                numbers = re.findall(r'\d+', count_text)
                return int(numbers[0]) if numbers else 0
        except:
            return 0
    
    def save_data(self, filename='twitter_job_data', format='csv'):
        """Save collected data to CSV file only"""
        if not self.tweets_data:
            print("No data to save!")
            return None
        
        if format.lower() == 'csv':
            # Use the enhanced CSV function
            df = save_to_csv(self.tweets_data, f'{filename}.csv')
            
            # Additional data validation and summary
            self.print_data_summary(df)
            
        return df
    
    def print_data_summary(self, df):
        """Print summary statistics of the saved data"""
        print(f"\n📈 Data Summary:")
        print(f"   • Total tweets: {len(df)}")
        print(f"   • Unique users: {df['Username'].nunique()}")
        print(f"   • Date range: {df['Date'].min()} to {df['Date'].max()}")
        print(f"   • Total likes: {df['Likes'].sum():,}")
        print(f"   • Total retweets: {df['Retweets'].sum():,}")
        print(f"   • Total replies: {df['Replies'].sum():,}")
        print(f"   • Average engagement per tweet: {(df['Likes'] + df['Retweets'] + df['Replies']).mean():.2f}")
    
    def analyze_data(self):
        """Perform basic analysis on collected data"""
        if not self.tweets_data:
            print("No data to analyze!")
            return
        
        df = pd.DataFrame(self.tweets_data)
        
        print("\n" + "="*50)
        print("📊 TWITTER DATA ANALYSIS REPORT")
        print("="*50)
        
        # Basic statistics
        print(f"📈 Total tweets collected: {len(df)}")
        print(f"👥 Unique users: {df['username'].nunique()}")
        
        # Top users by tweet count
        print("\n🔥 Top 10 Most Active Users:")
        top_users = df['username'].value_counts().head(10)
        for user, count in top_users.items():
            print(f"   @{user}: {count} tweets")
        
        # Most popular hashtags
        all_hashtags = []
        for hashtags in df['hashtags']:
            all_hashtags.extend(hashtags)
        
        if all_hashtags:
            hashtag_counts = pd.Series(all_hashtags).value_counts().head(10)
            print("\n#️⃣ Top 10 Hashtags:")
            for hashtag, count in hashtag_counts.items():
                print(f"   {hashtag}: {count} times")
        
        # Engagement statistics
        print(f"\n💯 Engagement Statistics:")
        print(f"   ❤️  Average likes: {df['likes'].mean():.2f}")
        print(f"   🔄 Average retweets: {df['retweets'].mean():.2f}")
        print(f"   💬 Average replies: {df['replies'].mean():.2f}")
        print(f"   👀 Average views: {df['views'].mean():.2f}")
        print(f"   🎯 Total engagement: {df[['likes', 'retweets', 'replies']].sum().sum()}")
        
        # Most engaging tweets
        df['total_engagement'] = df['likes'] + df['retweets'] + df['replies']
        top_tweets = df.nlargest(5, 'total_engagement')[['username', 'tweet', 'total_engagement']]
        
        print("\n🏆 Top 5 Most Engaging Tweets:")
        for idx, row in top_tweets.iterrows():
            print(f"   @{row['username']}: {row['total_engagement']} engagements")
            print(f"      \"{row['tweet'][:100]}...\"")
            print()
        
        return df
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()

def main():
    """Main function to run the Twitter scraper with CSV export only"""
    # Job-related hashtags to search for
    job_hashtags = ["naukri", "jobs", "jobseeker", "vacancy"]
    
    # Initialize scraper
    scraper = TwitterScraper(headless=False)  # Set to True for headless mode
    
    try:
        print("🚀 Starting Twitter Job Data Scraper...")
        print(f"🔍 Target hashtags: {', '.join(job_hashtags)}")
        
        # Search and scrape tweets
        scraper.search_hashtags(job_hashtags, max_tweets=2000)
        
        # Save data to CSV with specified format
        print("\n💾 Saving data to CSV...")
        df = scraper.save_data('twitter_job_analysis', 'csv')
        
        # No JSON saving as per user request
        
        # Perform analysis
        print("\n📊 Performing data analysis...")
        scraper.analyze_data()
        
        print("\n✅ Scraping completed successfully!")
        print(f"📁 File generated: twitter_job_analysis.csv")
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
