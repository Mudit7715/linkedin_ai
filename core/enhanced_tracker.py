import sqlite3
import pandas as pd
import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import json
from enum import Enum

class OutreachStatus(Enum):
    DISCOVERED = "discovered"
    CONNECTION_SENT = "connection_sent"
    CONNECTION_ACCEPTED = "connection_accepted"
    MESSAGE_SENT = "message_sent"
    MESSAGE_REPLIED = "message_replied"
    OPTED_OUT = "opted_out"

@dataclass
class Target:
    linkedin_id: str
    name: str
    company: str
    title: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: str = ""
    profile_summary: str = ""
    is_hiring_manager: bool = False
    ai_relevance_score: float = 0.0
    last_activity: Optional[datetime.datetime] = None
    profile_data: Optional[Dict[str, Any]] = None
    status: str = OutreachStatus.DISCOVERED.value
    opt_out: bool = False

@dataclass
class Connection:
    target_id: int
    sent_at: datetime.datetime
    accepted_at: Optional[datetime.datetime] = None
    connection_message: str = ""

@dataclass
class Message:
    target_id: int
    content: str
    sent_at: datetime.datetime
    replied_at: Optional[datetime.datetime] = None
    reply_content: Optional[str] = None
    message_type: str = "personalized"  # personalized, follow_up, thank_you

@dataclass
class Post:
    content: str
    scheduled_at: datetime.datetime
    published_at: Optional[datetime.datetime] = None
    approved: bool = False
    viral_insights: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None

class EnhancedLinkedInTracker:
    def __init__(self, db_path="linkedin_ai_outreach.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Targets table - potential connections
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                linkedin_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                company TEXT,
                title TEXT,
                email TEXT,
                phone TEXT,
                location TEXT,
                profile_summary TEXT,
                is_hiring_manager BOOLEAN DEFAULT FALSE,
                ai_relevance_score REAL DEFAULT 0.0,
                last_activity TIMESTAMP,
                profile_data TEXT,  -- JSON field
                status TEXT DEFAULT 'discovered',
                opt_out BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Connections table - tracking connection requests
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER NOT NULL,
                sent_at TIMESTAMP NOT NULL,
                accepted_at TIMESTAMP,
                connection_message TEXT,
                FOREIGN KEY (target_id) REFERENCES targets (id)
            )
        ''')
        
        # Messages table - DMs sent after connection
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                sent_at TIMESTAMP NOT NULL,
                replied_at TIMESTAMP,
                reply_content TEXT,
                message_type TEXT DEFAULT 'personalized',
                llm_prompt_used TEXT,
                FOREIGN KEY (target_id) REFERENCES targets (id)
            )
        ''')
        
        # Posts table - AI-generated content
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                scheduled_at TIMESTAMP NOT NULL,
                published_at TIMESTAMP,
                approved BOOLEAN DEFAULT FALSE,
                viral_insights TEXT,  -- JSON field
                performance_metrics TEXT,  -- JSON field
                llm_prompt_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Viral posts cache - trending content analysis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS viral_posts_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_url TEXT UNIQUE,
                author TEXT,
                content TEXT,
                reactions INTEGER,
                comments INTEGER,
                shares INTEGER,
                hashtags TEXT,  -- JSON array
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Daily limits tracker
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE,
                connections_sent INTEGER DEFAULT 0,
                messages_sent INTEGER DEFAULT 0,
                profile_views INTEGER DEFAULT 0
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_targets_status ON targets(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_targets_linkedin_id ON targets(linkedin_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_connections_target_id ON connections(target_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_target_id ON messages(target_id)')
        
        conn.commit()
        conn.close()
    
    def add_target(self, target: Target) -> Optional[int]:
        """Add a new target to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            profile_data_json = json.dumps(target.profile_data) if target.profile_data else None
            
            cursor.execute('''
                INSERT INTO targets (
                    linkedin_id, name, company, title, email, phone,
                    location, profile_summary, is_hiring_manager,
                    ai_relevance_score, last_activity, profile_data, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                target.linkedin_id, target.name, target.company, target.title,
                target.email, target.phone, target.location, target.profile_summary,
                target.is_hiring_manager, target.ai_relevance_score,
                target.last_activity, profile_data_json, target.status
            ))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"Target {target.linkedin_id} already exists")
            return None
        finally:
            conn.close()
    
    def update_target_status(self, linkedin_id: str, status: str):
        """Update the status of a target"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE targets 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE linkedin_id = ?
        ''', (status, linkedin_id))
        
        conn.commit()
        conn.close()
    
    def record_connection_sent(self, linkedin_id: str, message: str = "") -> bool:
        """Record that a connection request was sent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check daily limit
        today = datetime.date.today()
        cursor.execute('''
            INSERT OR IGNORE INTO daily_limits (date) VALUES (?)
        ''', (today,))
        
        cursor.execute('''
            SELECT connections_sent FROM daily_limits WHERE date = ?
        ''', (today,))
        
        daily_count = cursor.fetchone()[0]
        if daily_count >= 30:
            conn.close()
            return False
        
        # Get target ID
        cursor.execute('SELECT id FROM targets WHERE linkedin_id = ?', (linkedin_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        target_id = result[0]
        
        # Record connection
        cursor.execute('''
            INSERT INTO connections (target_id, sent_at, connection_message)
            VALUES (?, CURRENT_TIMESTAMP, ?)
        ''', (target_id, message))
        
        # Update daily count
        cursor.execute('''
            UPDATE daily_limits 
            SET connections_sent = connections_sent + 1
            WHERE date = ?
        ''', (today,))
        
        # Update target status
        cursor.execute('''
            UPDATE targets 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (OutreachStatus.CONNECTION_SENT.value, target_id))
        
        conn.commit()
        conn.close()
        return True
    
    def record_connection_accepted(self, linkedin_id: str):
        """Record that a connection request was accepted"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get target ID
        cursor.execute('SELECT id FROM targets WHERE linkedin_id = ?', (linkedin_id,))
        target_id = cursor.fetchone()[0]
        
        # Update connection record
        cursor.execute('''
            UPDATE connections 
            SET accepted_at = CURRENT_TIMESTAMP
            WHERE target_id = ? AND accepted_at IS NULL
        ''', (target_id,))
        
        # Update target status
        cursor.execute('''
            UPDATE targets 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (OutreachStatus.CONNECTION_ACCEPTED.value, target_id))
        
        conn.commit()
        conn.close()
    
    def record_message_sent(self, linkedin_id: str, content: str, 
                          message_type: str = "personalized", 
                          llm_prompt: str = "") -> bool:
        """Record that a message was sent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get target ID
        cursor.execute('SELECT id FROM targets WHERE linkedin_id = ?', (linkedin_id,))
        target_id = cursor.fetchone()[0]
        
        # Insert message
        cursor.execute('''
            INSERT INTO messages (
                target_id, content, sent_at, message_type, llm_prompt_used
            ) VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
        ''', (target_id, content, message_type, llm_prompt))
        
        # Update target status
        cursor.execute('''
            UPDATE targets 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (OutreachStatus.MESSAGE_SENT.value, target_id))
        
        conn.commit()
        conn.close()
        return True
    
    def get_pending_messages(self, hours_delay: int = 5) -> pd.DataFrame:
        """Get connections that are ready for messaging (accepted > X hours ago)"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                t.*, 
                c.accepted_at,
                JULIANDAY('now') - JULIANDAY(c.accepted_at) as days_since_accept
            FROM targets t
            JOIN connections c ON t.id = c.target_id
            WHERE c.accepted_at IS NOT NULL
                AND t.status = ?
                AND JULIANDAY('now') - JULIANDAY(c.accepted_at) >= ?
                AND t.opt_out = 0
                AND NOT EXISTS (
                    SELECT 1 FROM messages m WHERE m.target_id = t.id
                )
            ORDER BY c.accepted_at
        '''
        
        df = pd.read_sql_query(query, conn, params=(
            OutreachStatus.CONNECTION_ACCEPTED.value,
            hours_delay / 24.0
        ))
        conn.close()
        return df
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        analytics = {}
        
        # Target stats
        cursor.execute('SELECT COUNT(*) FROM targets WHERE opt_out = 0')
        analytics['total_targets'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM targets WHERE is_hiring_manager = 1')
        analytics['hiring_managers'] = cursor.fetchone()[0]
        
        # Connection stats
        cursor.execute('SELECT COUNT(*) FROM connections')
        analytics['connections_sent'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM connections WHERE accepted_at IS NOT NULL')
        analytics['connections_accepted'] = cursor.fetchone()[0]
        
        # Message stats
        cursor.execute('SELECT COUNT(*) FROM messages')
        analytics['messages_sent'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM messages WHERE replied_at IS NOT NULL')
        analytics['messages_replied'] = cursor.fetchone()[0]
        
        # Calculate rates
        if analytics['connections_sent'] > 0:
            analytics['acceptance_rate'] = (
                analytics['connections_accepted'] / analytics['connections_sent']
            )
        else:
            analytics['acceptance_rate'] = 0
            
        if analytics['messages_sent'] > 0:
            analytics['reply_rate'] = (
                analytics['messages_replied'] / analytics['messages_sent']
            )
        else:
            analytics['reply_rate'] = 0
        
        # Posts stats
        cursor.execute('SELECT COUNT(*) FROM posts WHERE approved = 1')
        analytics['posts_published'] = cursor.fetchone()[0]
        
        # Daily stats
        cursor.execute('''
            SELECT connections_sent, messages_sent 
            FROM daily_limits 
            WHERE date = ?
        ''', (datetime.date.today(),))
        
        result = cursor.fetchone()
        if result:
            analytics['today_connections'] = result[0]
            analytics['today_messages'] = result[1]
        else:
            analytics['today_connections'] = 0
            analytics['today_messages'] = 0
        
        # Get today's messages
        cursor.execute('''
            SELECT messages_sent
            FROM daily_limits 
            WHERE date = ?
        ''', (datetime.date.today(),))
        result = cursor.fetchone()
        analytics['today_messages'] = result[0] if result else 0
        
        conn.close()
        return analytics
    
    def opt_out_target(self, linkedin_id: str):
        """Mark a target as opted out"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE targets 
            SET opt_out = 1, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE linkedin_id = ?
        ''', (OutreachStatus.OPTED_OUT.value, linkedin_id))
        
        conn.commit()
        conn.close()
    
    def get_targets_for_outreach(self, limit: int = 30) -> pd.DataFrame:
        """Get targets ready for connection requests"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM targets 
            WHERE status = ? 
                AND opt_out = 0 
                AND ai_relevance_score >= 0.5
            ORDER BY ai_relevance_score DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(OutreachStatus.DISCOVERED.value, limit))
        conn.close()
        return df
    
    def record_post_published(self, post_id: int):
        """Mark a post as published"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE posts 
            SET published_at = CURRENT_TIMESTAMP, approved = 1
            WHERE id = ?
        ''', (post_id,))
        
        conn.commit()
        conn.close()
    
    def get_pending_post(self) -> Optional[Dict[str, Any]]:
        """Get the latest unpublished post for approval"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, content, scheduled_at, viral_insights
            FROM posts 
            WHERE approved = 0 AND published_at IS NULL
            ORDER BY scheduled_at DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'content': result[1],
                'scheduled_at': result[2],
                'viral_insights': json.loads(result[3]) if result[3] else None
            }
        return None
    
    def update_post_content(self, post_id: int, new_content: str):
        """Update post content before publishing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE posts 
            SET content = ?
            WHERE id = ?
        ''', (new_content, post_id))
        
        conn.commit()
        conn.close()
    
    def opt_out_target(self, linkedin_id: str):
        """Mark a target as opted out"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE targets 
            SET opt_out = 1, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE linkedin_id = ?
        ''', (OutreachStatus.OPTED_OUT.value, linkedin_id))
        
        conn.commit()
        conn.close()
