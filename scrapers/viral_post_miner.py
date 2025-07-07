import time
import random
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
from dataclasses import dataclass
import sqlite3
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ViralPost:
    post_url: str
    author: str
    author_title: str
    content: str
    reactions: int
    comments: int
    shares: int
    hashtags: List[str]
    posted_time: str
    engagement_rate: float

class ViralPostMiner:
    def __init__(self, driver: webdriver.Chrome = None):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10) if driver else None
        self.ai_hashtags = [
            "#AI", "#ArtificialIntelligence", "#MachineLearning", "#DeepLearning",
            "#DataScience", "#NeuralNetworks", "#LLM", "#GenerativeAI", "#AIEthics",
            "#MLOps", "#ComputerVision", "#NLP", "#ReinforcementLearning"
        ]
        
    def set_driver(self, driver: webdriver.Chrome):
        """Set the driver if not provided during initialization"""
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        
    def mine_viral_posts(self, hours_back: int = 24) -> List[ViralPost]:
        """Mine viral AI-related posts from the last N hours"""
        viral_posts = []
        
        for hashtag in self.ai_hashtags[:5]:  # Limit to avoid rate limiting
            try:
                posts = self._search_hashtag_posts(hashtag)
                
                for post in posts:
                    if self._is_recent_post(post, hours_back):
                        viral_post = self._extract_post_data(post)
                        if viral_post and viral_post.engagement_rate > 0.05:  # 5% engagement threshold
                            viral_posts.append(viral_post)
                            
                time.sleep(random.uniform(3, 5))  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error mining posts for {hashtag}: {e}")
                continue
                
        # Sort by engagement rate
        viral_posts.sort(key=lambda x: x.engagement_rate, reverse=True)
        
        # Cache the results
        if viral_posts:
            self._cache_viral_posts(viral_posts[:20])
        
        return viral_posts[:5]  # Return top 5
    
    def _search_hashtag_posts(self, hashtag: str) -> List[Any]:
        """Search for posts with a specific hashtag"""
        search_url = f"https://www.linkedin.com/search/results/content/?keywords={hashtag}&sortBy=%22date_posted%22"
        self.driver.get(search_url)
        time.sleep(random.uniform(3, 5))
        
        try:
            # Wait for posts to load
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-shared-update-v2")))
            
            # Get all posts
            posts = self.driver.find_elements(By.CSS_SELECTOR, ".feed-shared-update-v2")
            return posts[:10]  # Limit per hashtag
            
        except TimeoutException:
            logger.warning(f"No posts found for {hashtag}")
            return []
    
    def _is_recent_post(self, post_element, hours_back: int) -> bool:
        """Check if post is within the specified time window"""
        try:
            time_element = post_element.find_element(By.CSS_SELECTOR, ".feed-shared-actor__sub-description")
            time_text = time_element.text.strip()
            
            # Parse relative time (e.g., "2h", "1d", "3w")
            if "h" in time_text or "hour" in time_text:
                hours = int(''.join(filter(str.isdigit, time_text)))
                return hours <= hours_back
            elif "m" in time_text or "minute" in time_text:
                return True  # Recent enough
            elif "d" in time_text or "day" in time_text:
                days = int(''.join(filter(str.isdigit, time_text)))
                return days * 24 <= hours_back
            else:
                return False
                
        except Exception:
            return False
    
    def _extract_post_data(self, post_element) -> ViralPost:
        """Extract detailed data from a post"""
        try:
            # Author info
            author_element = post_element.find_element(By.CSS_SELECTOR, ".feed-shared-actor__name")
            author = author_element.text.strip()
            
            author_title_element = post_element.find_element(By.CSS_SELECTOR, ".feed-shared-actor__description")
            author_title = author_title_element.text.strip()
            
            # Post content
            try:
                content_element = post_element.find_element(By.CSS_SELECTOR, ".feed-shared-text")
                content = content_element.text.strip()
            except:
                content = ""
            
            # Extract hashtags
            hashtags = self._extract_hashtags(content)
            
            # Engagement metrics
            reactions = self._extract_reaction_count(post_element)
            comments = self._extract_comment_count(post_element)
            shares = self._extract_share_count(post_element)
            
            # Post URL
            post_url = self._extract_post_url(post_element)
            
            # Time
            time_element = post_element.find_element(By.CSS_SELECTOR, ".feed-shared-actor__sub-description")
            posted_time = time_element.text.strip()
            
            # Calculate engagement rate (simplified)
            total_engagement = reactions + comments + shares
            engagement_rate = total_engagement / 1000.0  # Normalize by 1000
            
            return ViralPost(
                post_url=post_url,
                author=author,
                author_title=author_title,
                content=content,
                reactions=reactions,
                comments=comments,
                shares=shares,
                hashtags=hashtags,
                posted_time=posted_time,
                engagement_rate=engagement_rate
            )
            
        except Exception as e:
            logger.error(f"Error extracting post data: {e}")
            return None
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from post content"""
        hashtag_pattern = r'#\w+'
        return re.findall(hashtag_pattern, content)
    
    def _extract_reaction_count(self, post_element) -> int:
        """Extract reaction count from post"""
        try:
            reaction_element = post_element.find_element(
                By.CSS_SELECTOR, 
                ".social-details-social-counts__reactions-count"
            )
            count_text = reaction_element.text.strip()
            return self._parse_count(count_text)
        except:
            return 0
    
    def _extract_comment_count(self, post_element) -> int:
        """Extract comment count from post"""
        try:
            comment_element = post_element.find_element(
                By.CSS_SELECTOR,
                ".social-details-social-counts__comments"
            )
            count_text = comment_element.text.strip()
            return self._parse_count(count_text)
        except:
            return 0
    
    def _extract_share_count(self, post_element) -> int:
        """Extract share count from post"""
        try:
            share_element = post_element.find_element(
                By.CSS_SELECTOR,
                ".social-details-social-counts__item--with-social-proof"
            )
            count_text = share_element.text.strip()
            return self._parse_count(count_text)
        except:
            return 0
    
    def _extract_post_url(self, post_element) -> str:
        """Extract post URL"""
        try:
            # Get parent article ID
            article = post_element.find_element(By.XPATH, ".//ancestor::article")
            post_id = article.get_attribute("data-id")
            if post_id:
                return f"https://www.linkedin.com/feed/update/{post_id}"
        except:
            pass
        
        try:
            # Alternative: find timestamp link
            activity_link = post_element.find_element(
                By.CSS_SELECTOR,
                ".feed-shared-actor__sub-description a"
            )
            return activity_link.get_attribute('href')
        except:
            return ""
    
    def _parse_count(self, count_text: str) -> int:
        """Parse count text (handles 1.2K, 10K, etc.)"""
        if not count_text:
            return 0
            
        count_text = count_text.strip().lower()
        
        # Remove commas
        count_text = count_text.replace(',', '')
        
        # Handle K (thousands)
        if 'k' in count_text:
            try:
                number = float(re.findall(r'[\d.]+', count_text)[0])
                return int(number * 1000)
            except:
                return 0
                
        # Handle M (millions)
        if 'm' in count_text:
            try:
                number = float(re.findall(r'[\d.]+', count_text)[0])
                return int(number * 1000000)
            except:
                return 0
                
        # Try to parse as regular number
        try:
            return int(count_text)
        except:
            # Extract just numbers
            numbers = re.findall(r'\d+', count_text)
            if numbers:
                return int(numbers[0])
            return 0
    
    def _cache_viral_posts(self, posts: List[ViralPost]):
        """Cache viral posts in database"""
        try:
            # Import here to avoid circular imports
            import os
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from core.enhanced_tracker import EnhancedLinkedInTracker
            
            tracker = EnhancedLinkedInTracker()
            conn = sqlite3.connect(tracker.db_path)
            cursor = conn.cursor()
            
            for post in posts:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO viral_posts_cache 
                        (post_url, author, content, reactions, comments, shares, hashtags)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        post.post_url,
                        post.author,
                        post.content,
                        post.reactions,
                        post.comments,
                        post.shares,
                        json.dumps(post.hashtags)
                    ))
                except Exception as e:
                    logger.error(f"Error caching post: {e}")
                    
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error in cache operation: {e}")
    
    def get_cached_viral_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get cached viral posts from database"""
        try:
            import os
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from core.enhanced_tracker import EnhancedLinkedInTracker
            
            tracker = EnhancedLinkedInTracker()
            conn = sqlite3.connect(tracker.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT post_url, author, content, reactions, comments, shares, hashtags
                FROM viral_posts_cache
                ORDER BY reactions + comments + shares DESC
                LIMIT ?
            ''', (limit,))
            
            posts = []
            for row in cursor.fetchall():
                posts.append({
                    'post_url': row[0],
                    'author': row[1],
                    'content': row[2],
                    'reactions': row[3],
                    'comments': row[4],
                    'shares': row[5],
                    'hashtags': json.loads(row[6]) if row[6] else [],
                    'engagement': row[3] + row[4] + row[5]
                })
                
            conn.close()
            return posts
        except Exception as e:
            logger.error(f"Error getting cached posts: {e}")
            return []
    
    def analyze_viral_patterns(self, posts: List[ViralPost]) -> Dict[str, Any]:
        """Analyze patterns in viral posts"""
        if not posts:
            return {}
            
        patterns = {
            'avg_content_length': sum(len(p.content) for p in posts) / len(posts),
            'avg_engagement_rate': sum(p.engagement_rate for p in posts) / len(posts),
            'common_hashtags': {},
            'content_patterns': [],
            'best_posting_times': []
        }
        
        # Analyze hashtags
        hashtag_counts = {}
        for post in posts:
            for hashtag in post.hashtags:
                hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
                
        patterns['common_hashtags'] = dict(sorted(
            hashtag_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])
        
        # Analyze content patterns
        hook_patterns = [
            "unpopular opinion",
            "breaking",
            "just discovered",
            "warning",
            "stop",
            "nobody talks about",
            "here's why",
            "the truth about",
            "I was wrong"
        ]
        
        for pattern in hook_patterns:
            count = sum(1 for p in posts if pattern.lower() in p.content.lower())
            if count > 0:
                patterns['content_patterns'].append({
                    'pattern': pattern,
                    'frequency': count / len(posts),
                    'avg_engagement': sum(p.engagement_rate for p in posts if pattern.lower() in p.content.lower()) / count
                })
        
        # Sort content patterns by engagement
        patterns['content_patterns'].sort(key=lambda x: x['avg_engagement'], reverse=True)
        
        return patterns
