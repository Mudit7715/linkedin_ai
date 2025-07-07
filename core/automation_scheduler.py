import time
import random
import logging
import schedule
import sqlite3
import pandas as pd
import yaml
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import os
from dotenv import load_dotenv

from .enhanced_tracker import EnhancedLinkedInTracker, Target, OutreachStatus
from .ollama_connector import OllamaConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class AutomationScheduler:
    def __init__(self):
        self.tracker = EnhancedLinkedInTracker()
        self.ollama = OllamaConnector()
        self.linkedin_email = os.getenv('LINKEDIN_EMAIL')
        self.linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        self.scraper = None
        self.viral_miner = None
        self.daily_connection_count = 0
        self.max_daily_connections = 30
        self.message_delay_hours = 5
        self.is_running = False
        
    def initialize_scraper(self):
        """Initialize LinkedIn scraper with login"""
        if not self.scraper:
            # Import here to avoid circular imports
            from ..scrapers.linkedin_scraper import LinkedInScraper
            from ..scrapers.viral_post_miner import ViralPostMiner
            
            self.scraper = LinkedInScraper(
                self.linkedin_email, 
                self.linkedin_password,
                headless=True
            )
            if not self.scraper.login():
                logger.error("Failed to login to LinkedIn")
                return False
                
            # Initialize viral miner with same driver
            self.viral_miner = ViralPostMiner(self.scraper.driver)
            
        return True
    
    def run_nightly_scraper(self):
        """Nightly job to discover new targets"""
        logger.info("Starting nightly scraper job...")
        
        if not self.initialize_scraper():
            return
            
        # Load target companies from config
        with open('config/prompts.yml', 'r') as f:
            config = yaml.safe_load(f)
            
        companies = (
            config['target_companies']['global_leaders'] + 
            config['target_companies']['india_presence']
        )
        
        # Scrape profiles
        profiles = self.scraper.search_targets(companies[:10])  # Limit for safety
        
        # Process and store profiles
        for profile_data in profiles:
            target = self._profile_to_target(profile_data)
            
            # Use Ollama to analyze profile
            analysis = self._analyze_profile_with_llm(profile_data)
            
            if analysis:
                target.is_hiring_manager = analysis.get('is_hiring_manager', False)
                target.ai_relevance_score = analysis.get('ai_relevance_score', 0.0)
                
            # Add to database
            self.tracker.add_target(target)
            time.sleep(random.uniform(2, 5))
            
        logger.info(f"Discovered {len(profiles)} new targets")
    
    def run_morning_viral_post_job(self):
        """Morning job to generate and schedule viral post"""
        logger.info("Starting morning viral post job...")
        
        if not self.initialize_scraper():
            return
            
        # Mine viral posts
        viral_posts = self.viral_miner.mine_viral_posts(hours_back=24)
        
        if not viral_posts:
            # Use cached posts
            cached_posts = self.viral_miner.get_cached_viral_posts()
            viral_insights = json.dumps(cached_posts[:5])
        else:
            # Analyze patterns
            patterns = self.viral_miner.analyze_viral_patterns(viral_posts)
            viral_insights = json.dumps({
                'top_posts': [
                    {
                        'content': p.content[:200],
                        'engagement': p.engagement_rate,
                        'hashtags': p.hashtags
                    } for p in viral_posts[:3]
                ],
                'patterns': patterns
            })
        
        # Generate post with Ollama
        generated_post = self.ollama.generate(
            'viral_post',
            {'viral_insights': viral_insights}
        )
        
        if generated_post:
            # Store in database for approval
            conn = sqlite3.connect(self.tracker.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO posts (content, scheduled_at, viral_insights, llm_prompt_used)
                VALUES (?, ?, ?, ?)
            ''', (
                generated_post,
                datetime.now(),
                viral_insights,
                'viral_post'
            ))
            conn.commit()
            conn.close()
            
            logger.info("Viral post generated and awaiting approval")
            logger.info(f"Post preview: {generated_post[:100]}...")
    
    def run_connection_requests(self):
        """Send connection requests throughout the day"""
        logger.info("Running connection request job...")
        
        if self.daily_connection_count >= self.max_daily_connections:
            logger.info("Daily connection limit reached")
            return
            
        if not self.initialize_scraper():
            return
            
        # Get targets ready for outreach
        conn = sqlite3.connect(self.tracker.db_path)
        query = '''
            SELECT * FROM targets 
            WHERE status = ? 
                AND opt_out = 0 
                AND ai_relevance_score >= 0.5
            ORDER BY ai_relevance_score DESC
            LIMIT ?
        '''
        
        remaining_today = self.max_daily_connections - self.daily_connection_count
        targets_df = pd.read_sql_query(
            query, 
            conn, 
            params=(OutreachStatus.DISCOVERED.value, remaining_today)
        )
        conn.close()
        
        for _, target in targets_df.iterrows():
            if self.daily_connection_count >= self.max_daily_connections:
                break
                
            # Generate personalized connection request
            connection_message = self.ollama.generate(
                'connection_request',
                {
                    'name': target['name'],
                    'company': target['company'],
                    'title': target['title'],
                    'summary': target['profile_summary'][:200]
                }
            )
            
            if connection_message:
                # Send connection request (simulated here)
                success = self._send_connection_request(
                    target['linkedin_id'], 
                    connection_message
                )
                
                if success:
                    self.tracker.record_connection_sent(
                        target['linkedin_id'], 
                        connection_message
                    )
                    self.daily_connection_count += 1
                    logger.info(f"Sent connection request to {target['name']} ({self.daily_connection_count}/{self.max_daily_connections})")
                    
                # Random delay between connections
                time.sleep(random.uniform(30, 90))
        
        logger.info(f"Connection request job completed. Sent {self.daily_connection_count} requests today.")
    
    def check_accepted_connections(self):
        """Check for newly accepted connections and schedule messages"""
        logger.info("Checking for accepted connections...")
        
        if not self.initialize_scraper():
            return
            
        # Check LinkedIn for accepted connections
        accepted_profiles = self.scraper.check_accepted_connections()
        
        for linkedin_id in accepted_profiles:
            # Update status in database
            self.tracker.record_connection_accepted(linkedin_id)
            logger.info(f"Connection accepted: {linkedin_id}")
            
        # Get connections ready for messaging (after delay)
        pending_messages = self.tracker.get_pending_messages(hours_delay=self.message_delay_hours)
        
        for _, target in pending_messages.iterrows():
            # Generate personalized message
            profile_data = json.loads(target['profile_data']) if target['profile_data'] else {}
            
            message = self.ollama.generate(
                'personalized_message',
                {
                    'name': target['name'],
                    'company': target['company'],
                    'title': target['title'],
                    'profile_data': json.dumps(profile_data),
                    'recent_activity': json.dumps(profile_data.get('recent_activity', []))
                }
            )
            
            if message:
                # Send message
                profile_url = f"https://www.linkedin.com/in/{target['linkedin_id']}"
                success = self._send_message(profile_url, message)
                
                if success:
                    self.tracker.record_message_sent(
                        target['linkedin_id'],
                        message,
                        message_type='personalized',
                        llm_prompt='personalized_message'
                    )
                    logger.info(f"Sent message to {target['name']}")
                    
                # Delay between messages
                time.sleep(random.uniform(60, 120))
    
    def _profile_to_target(self, profile_data) -> Target:
        """Convert ProfileData to Target object"""
        return Target(
            linkedin_id=profile_data.linkedin_id,
            name=profile_data.name,
            company=profile_data.company,
            title=profile_data.title,
            email=profile_data.email,
            phone=profile_data.phone,
            location=profile_data.location,
            profile_summary=profile_data.summary,
            profile_data={
                'experience': profile_data.experience,
                'skills': profile_data.skills,
                'recent_activity': profile_data.recent_activity
            }
        )
    
    def _analyze_profile_with_llm(self, profile_data) -> Optional[Dict[str, Any]]:
        """Use LLM to analyze profile for hiring manager status and AI relevance"""
        profile_html = f"""
        Name: {profile_data.name}
        Title: {profile_data.title}
        Company: {profile_data.company}
        Location: {profile_data.location}
        Summary: {profile_data.summary}
        Skills: {', '.join(profile_data.skills or [])}
        Recent Activity: {json.dumps(profile_data.recent_activity or [])}
        """
        
        analysis = self.ollama.generate(
            'profile_analyzer',
            {'profile_html': profile_html}
        )
        
        if analysis:
            # Parse the LLM response
            try:
                # Simple parsing - in production, use structured output
                is_hiring_manager = 'hiring manager: true' in analysis.lower() or 'true' in analysis.lower()
                
                # Extract score
                import re
                score_match = re.search(r'score:?\s*(\d*\.?\d+)', analysis.lower())
                ai_relevance_score = float(score_match.group(1)) if score_match else 0.5
                
                return {
                    'is_hiring_manager': is_hiring_manager,
                    'ai_relevance_score': min(1.0, max(0.0, ai_relevance_score))
                }
            except:
                return {'is_hiring_manager': False, 'ai_relevance_score': 0.5}
        
        return None
    
    def _send_connection_request(self, linkedin_id: str, message: str) -> bool:
        """Send connection request via LinkedIn"""
        profile_url = f"https://www.linkedin.com/in/{linkedin_id}"
        return self.scraper.send_connection_request(profile_url, message)
    
    def _send_message(self, profile_url: str, message: str) -> bool:
        """Send direct message via LinkedIn"""
        return self.scraper.send_message(profile_url, message)
    
    def start(self):
        """Start the automation scheduler"""
        self.is_running = True
        
        # Schedule jobs
        schedule.every().day.at("02:00").do(self.run_nightly_scraper)
        schedule.every().day.at("07:00").do(self.run_morning_viral_post_job)
        schedule.every(30).minutes.do(self.run_connection_requests)
        schedule.every(15).minutes.do(self.check_accepted_connections)
        
        # Reset daily counter at midnight
        schedule.every().day.at("00:00").do(self._reset_daily_counter)
        
        logger.info("Automation scheduler started. Running jobs...")
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the automation scheduler"""
        self.is_running = False
        if self.scraper:
            self.scraper.close()
        logger.info("Automation scheduler stopped.")
    
    def _reset_daily_counter(self):
        """Reset daily connection counter"""
        self.daily_connection_count = 0
        logger.info("Daily connection counter reset.")
