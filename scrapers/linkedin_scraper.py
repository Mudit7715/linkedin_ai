import time
import random
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
from datetime import datetime
import re
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProfileData:
    linkedin_id: str
    name: str
    title: str
    company: str
    location: str
    email: Optional[str] = None
    phone: Optional[str] = None
    profile_url: str = ""
    summary: str = ""
    experience: List[Dict] = None
    skills: List[str] = None
    recent_activity: List[Dict] = None

class LinkedInScraper:
    def __init__(self, email: str, password: str, headless: bool = False):
        self.email = email
        self.password = password
        self.driver = None
        self.wait = None
        self.headless = headless
        self.setup_driver()
        
        # Load configuration
        with open('config/prompts.yml', 'r') as f:
            self.config = yaml.safe_load(f)
            
    def setup_driver(self):
        """Setup Chrome driver with anti-detection measures"""
        options = Options()
        
        # Anti-detection settings
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        
        if self.headless:
            options.add_argument('--headless')
            
        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
        
    def login(self) -> bool:
        """Login to LinkedIn"""
        try:
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(random.uniform(2, 4))
            
            # Enter credentials
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field.send_keys(self.email)
            time.sleep(random.uniform(0.5, 1.5))
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.password)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(random.uniform(3, 5))
            
            # Check if logged in
            return "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def search_targets(self, companies: List[str], keywords: List[str] = None) -> List[ProfileData]:
        """Search for AI hiring managers at target companies"""
        if keywords is None:
            keywords = ["hiring manager", "engineering manager", "AI", "ML", "machine learning"]
            
        targets = []
        
        for company in companies:
            try:
                # Build search query
                search_query = f'"{company}" India'
                if keywords:
                    search_query += " " + " OR ".join([f'"{k}"' for k in keywords])
                
                # Perform search
                search_url = f"https://www.linkedin.com/search/results/people/?keywords={search_query}"
                self.driver.get(search_url)
                time.sleep(random.uniform(3, 5))
                
                # Extract profiles from search results
                profiles = self._extract_search_results()
                
                for profile_url in profiles[:10]:  # Limit per company
                    profile_data = self.scrape_profile(profile_url)
                    if profile_data and self._is_relevant_target(profile_data):
                        targets.append(profile_data)
                        time.sleep(random.uniform(5, 10))  # Rate limiting
                        
            except Exception as e:
                logger.error(f"Error searching {company}: {e}")
                continue
                
        return targets
    
    def _extract_search_results(self) -> List[str]:
        """Extract profile URLs from search results"""
        profile_urls = []
        
        try:
            # Wait for results to load
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-results-container")))
            
            # Find all profile links
            links = self.driver.find_elements(By.CSS_SELECTOR, "a.app-aware-link")
            
            for link in links:
                href = link.get_attribute('href')
                if href and '/in/' in href and 'linkedin.com/in/' in href:
                    # Clean URL
                    profile_url = href.split('?')[0]
                    if profile_url not in profile_urls:
                        profile_urls.append(profile_url)
                        
        except Exception as e:
            logger.error(f"Error extracting search results: {e}")
            
        return profile_urls
    
    def scrape_profile(self, profile_url: str) -> Optional[ProfileData]:
        """Scrape detailed profile information"""
        try:
            self.driver.get(profile_url)
            time.sleep(random.uniform(3, 5))
            
            # Extract LinkedIn ID from URL
            linkedin_id = profile_url.split('/in/')[-1].strip('/')
            
            # Wait for profile to load
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "pv-top-card")))
            
            # Extract basic info
            name = self._safe_extract("h1", By.TAG_NAME)
            title = self._safe_extract(".pv-top-card--list", By.CSS_SELECTOR)
            location = self._safe_extract(".pv-top-card__location", By.CSS_SELECTOR)
            
            # Extract company from experience section
            company = self._extract_current_company()
            
            # Extract summary
            summary = self._extract_summary()
            
            # Extract contact info (if available)
            email, phone = self._extract_contact_info()
            
            # Extract experience
            experience = self._extract_experience()
            
            # Extract skills
            skills = self._extract_skills()
            
            # Extract recent activity
            recent_activity = self._extract_recent_activity()
            
            return ProfileData(
                linkedin_id=linkedin_id,
                name=name,
                title=title,
                company=company,
                location=location,
                email=email,
                phone=phone,
                profile_url=profile_url,
                summary=summary,
                experience=experience,
                skills=skills,
                recent_activity=recent_activity
            )
            
        except Exception as e:
            logger.error(f"Error scraping profile {profile_url}: {e}")
            return None
    
    def _safe_extract(self, selector: str, by: By = By.CSS_SELECTOR) -> str:
        """Safely extract text from element"""
        try:
            element = self.driver.find_element(by, selector)
            return element.text.strip()
        except:
            return ""
    
    def _extract_current_company(self) -> str:
        """Extract current company from experience section"""
        try:
            # Try to find current position
            experience_section = self.driver.find_element(By.ID, "experience")
            current_position = experience_section.find_element(By.CSS_SELECTOR, ".pv-entity__position-group-pager")
            company_element = current_position.find_element(By.CSS_SELECTOR, ".pv-entity__secondary-title")
            return company_element.text.strip()
        except:
            # Fallback: try alternate selectors
            try:
                company_element = self.driver.find_element(By.CSS_SELECTOR, "[aria-label*='Current company']")
                return company_element.text.strip()
            except:
                return ""
    
    def _extract_summary(self) -> str:
        """Extract profile summary/about section"""
        try:
            # Click "Show more" if present
            try:
                show_more = self.driver.find_element(By.CSS_SELECTOR, ".inline-show-more-text__button")
                show_more.click()
                time.sleep(1)
            except:
                pass
                
            summary_element = self.driver.find_element(By.CSS_SELECTOR, ".pv-shared-text-with-see-more")
            return summary_element.text.strip()
        except:
            return ""
    
    def _extract_contact_info(self) -> tuple:
        """Extract contact information if available"""
        email, phone = None, None
        
        try:
            # Try to open contact info modal
            contact_button = self.driver.find_element(By.CSS_SELECTOR, "a[data-control-name='contact_see_more']") 
            contact_button.click()
            time.sleep(2)
            
            # Extract email
            try:
                email_element = self.driver.find_element(By.CSS_SELECTOR, ".ci-email .pv-contact-info__contact-link")
                email = email_element.text.strip()
            except:
                pass
                
            # Extract phone
            try:
                phone_element = self.driver.find_element(By.CSS_SELECTOR, ".ci-phone .pv-contact-info__contact-link")
                phone = phone_element.text.strip()
            except:
                pass
                
            # Close modal
            close_button = self.driver.find_element(By.CSS_SELECTOR, ".artdeco-modal__dismiss")
            close_button.click()
            
        except:
            pass
            
        return email, phone
    
    def _extract_experience(self) -> List[Dict]:
        """Extract work experience"""
        experience = []
        
        try:
            experience_section = self.driver.find_element(By.ID, "experience")
            positions = experience_section.find_elements(By.CSS_SELECTOR, ".pv-entity__position-group-pager")
            
            for position in positions[:5]:  # Limit to 5 most recent
                try:
                    exp = {
                        'title': position.find_element(By.CSS_SELECTOR, "h3").text.strip(),
                        'company': position.find_element(By.CSS_SELECTOR, ".pv-entity__secondary-title").text.strip(),
                        'duration': position.find_element(By.CSS_SELECTOR, ".pv-entity__date-range").text.strip(),
                        'description': ""
                    }
                    
                    try:
                        exp['description'] = position.find_element(By.CSS_SELECTOR, ".pv-entity__description").text.strip()
                    except:
                        pass
                        
                    experience.append(exp)
                except:
                    continue
                    
        except:
            pass
            
        return experience
    
    def _extract_skills(self) -> List[str]:
        """Extract skills from profile"""
        skills = []
        
        try:
            # Try to find skills section
            skills_section = self.driver.find_element(By.CSS_SELECTOR, ".pv-skill-categories-section")
            skill_elements = skills_section.find_elements(By.CSS_SELECTOR, ".pv-skill-category-entity__name")
            
            for skill in skill_elements[:10]:  # Top 10 skills
                skills.append(skill.text.strip())
                
        except:
            pass
            
        return skills
    
    def _extract_recent_activity(self) -> List[Dict]:
        """Extract recent activity/posts"""
        activities = []
        
        try:
            # Navigate to activity tab
            activity_tab = self.driver.find_element(By.CSS_SELECTOR, "a[data-control-name='recent_activity_details_all']")
            activity_tab.click()
            time.sleep(2)
            
            # Get recent posts
            posts = self.driver.find_elements(By.CSS_SELECTOR, ".feed-shared-update-v2")[:3]
            
            for post in posts:
                try:
                    activity = {
                        'type': 'post',
                        'content': post.find_element(By.CSS_SELECTOR, ".feed-shared-text").text.strip()[:200],
                        'time': post.find_element(By.CSS_SELECTOR, ".feed-shared-actor__sub-description").text.strip()
                    }
                    activities.append(activity)
                except:
                    continue
                    
        except:
            pass
            
        return activities
    
    def _is_relevant_target(self, profile_data: ProfileData) -> bool:
        """Check if profile is relevant for AI outreach"""
        if not profile_data:
            return False
            
        # Check location (India-based)
        if profile_data.location and 'india' not in profile_data.location.lower():
            return False
            
        # Check for hiring/management keywords
        hiring_keywords = self.config['scoring']['hiring_indicators']
        title_lower = profile_data.title.lower() if profile_data.title else ""
        
        is_hiring_related = any(keyword.lower() in title_lower for keyword in hiring_keywords)
        
        # Check for AI/ML relevance
        ai_keywords = (
            self.config['scoring']['ai_relevance_keywords']['high_value'] +
            self.config['scoring']['ai_relevance_keywords']['medium_value']
        )
        
        text_to_check = f"{profile_data.title} {profile_data.summary} {' '.join(profile_data.skills or [])}".lower()
        has_ai_relevance = any(keyword.lower() in text_to_check for keyword in ai_keywords)
        
        return is_hiring_related or has_ai_relevance
    
    def send_connection_request(self, profile_url: str, message: str) -> bool:
        """Send a connection request with personalized message"""
        try:
            self.driver.get(profile_url)
            time.sleep(random.uniform(3, 5))
            
            # Find connect button
            connect_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label*='Connect']"))
            )
            connect_button.click()
            time.sleep(1)
            
            # Add note
            add_note_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Add a note']")
            add_note_button.click()
            time.sleep(1)
            
            # Enter message
            message_field = self.driver.find_element(By.CSS_SELECTOR, "textarea[name='message']")
            message_field.send_keys(message)
            time.sleep(1)
            
            # Send request
            send_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Send now']")
            send_button.click()
            
            time.sleep(random.uniform(2, 4))
            return True
            
        except Exception as e:
            logger.error(f"Error sending connection request: {e}")
            return False
    
    def send_message(self, profile_url: str, message: str) -> bool:
        """Send a direct message to a connection"""
        try:
            self.driver.get(profile_url)
            time.sleep(random.uniform(3, 5))
            
            # Find message button
            message_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label*='Message']"))
            )
            message_button.click()
            time.sleep(2)
            
            # Enter message
            message_field = self.driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
            message_field.send_keys(message)
            time.sleep(1)
            
            # Send message
            send_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']") 
            send_button.click()
            
            time.sleep(random.uniform(2, 4))
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def check_accepted_connections(self) -> List[str]:
        """Check for newly accepted connection requests"""
        accepted_profiles = []
        
        try:
            # Go to My Network page
            self.driver.get("https://www.linkedin.com/mynetwork/invitation-manager/")
            time.sleep(random.uniform(3, 5))
            
            # Click on 'Accepted' tab
            accepted_tab = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Accepted invitations']") 
            accepted_tab.click()
            time.sleep(2)
            
            # Get accepted connection profiles
            connections = self.driver.find_elements(By.CSS_SELECTOR, ".invitation-card")
            
            for connection in connections[:10]:  # Check last 10
                try:
                    profile_link = connection.find_element(By.CSS_SELECTOR, "a[href*='/in/']") 
                    profile_url = profile_link.get_attribute('href')
                    linkedin_id = profile_url.split('/in/')[-1].strip('/')
                    accepted_profiles.append(linkedin_id)
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Error checking accepted connections: {e}")
            
        return accepted_profiles
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
