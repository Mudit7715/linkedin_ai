import pytest
import os
import tempfile
import yaml
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enhanced_tracker import EnhancedLinkedInTracker, Target
from core.ollama_connector import OllamaConnector
from core.automation_scheduler import AutomationScheduler

class TestIntegration:
    @pytest.fixture
    def test_environment(self):
        """Create test environment with mocked components"""
        # Create temporary config
        config = {
            'ollama': {
                'model': 'test-model',
                'temperature': 0.7
            },
            'prompts': {
                'connection_request': {
                    'system': 'Test system prompt',
                    'user': 'Test user prompt for {name}'
                },
                'personalized_message': {
                    'system': 'Test message system',
                    'user': 'Test message for {name}'
                }
            },
            'target_companies': {
                'global_leaders': ['TestCorp'],
                'india_presence': ['TestCorp India']
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tmp:
            yaml.dump(config, tmp)
            config_path = tmp.name
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        yield config_path, db_path
        
        # Cleanup
        os.unlink(config_path)
        os.unlink(db_path)
    
    @patch('selenium.webdriver.Chrome')
    @patch('requests.post')
    def test_full_pipeline(self, mock_post, mock_chrome, test_environment):
        """Test the full outreach pipeline"""
        config_path, db_path = test_environment
        
        # Mock Ollama responses
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {'response': 'Generated content'}
        )
        
        # Mock Chrome driver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Initialize components
        tracker = EnhancedLinkedInTracker(db_path)
        ollama = OllamaConnector(config_path)
        
        # Test target discovery and addition
        target = Target(
            linkedin_id="test123",
            name="Test User",
            company="TestCorp India",
            title="AI Manager",
            location="Bangalore, India",
            is_hiring_manager=True,
            ai_relevance_score=0.9
        )
        
        target_id = tracker.add_target(target)
        assert target_id is not None
        
        # Test connection request generation
        connection_msg = ollama.generate(
            'connection_request',
            {
                'name': target.name,
                'company': target.company,
                'title': target.title,
                'summary': 'AI expert'
            }
        )
        assert connection_msg == 'Generated content'
        
        # Test recording connection sent
        success = tracker.record_connection_sent(target.linkedin_id, connection_msg)
        assert success == True
        
        # Test acceptance and message flow
        tracker.record_connection_accepted(target.linkedin_id)
        
        # Get pending messages
        pending = tracker.get_pending_messages(hours_delay=0)  # No delay for test
        assert len(pending) == 1
        
        # Generate personalized message
        personal_msg = ollama.generate(
            'personalized_message',
            {
                'name': target.name,
                'company': target.company,
                'title': target.title,
                'profile_data': '{}',
                'recent_activity': 'None'
            }
        )
        assert personal_msg == 'Generated content'
        
        # Record message sent
        tracker.record_message_sent(
            target.linkedin_id,
            personal_msg,
            'personalized',
            'personalized_message'
        )
        
        # Verify analytics
        analytics = tracker.get_analytics()
        assert analytics['total_targets'] == 1
        assert analytics['connections_sent'] == 1
        assert analytics['connections_accepted'] == 1
        assert analytics['messages_sent'] == 1
        assert analytics['acceptance_rate'] == 1.0
    
    @patch('requests.get')
    def test_ollama_health_check_integration(self, mock_get, test_environment):
        """Test Ollama health check in integration"""
        config_path, _ = test_environment
        
        # Mock healthy Ollama
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                'models': [
                    {'name': 'test-model:latest'}
                ]
            }
        )
        
        ollama = OllamaConnector(config_path)
        assert ollama.check_health() == True
    
    def test_database_migration(self, test_environment):
        """Test database migration from legacy format"""
        _, db_path = test_environment
        
        # Create legacy database structure
        import sqlite3
        legacy_conn = sqlite3.connect(':memory:')
        cursor = legacy_conn.cursor()
        
        # Create legacy tables
        cursor.execute('''
            CREATE TABLE contacts (
                id INTEGER PRIMARY KEY,
                linkedin_id TEXT,
                name TEXT,
                company TEXT,
                title TEXT,
                connection_sent TIMESTAMP,
                connection_accepted TIMESTAMP,
                message_sent TIMESTAMP,
                message_replied TIMESTAMP,
                notes TEXT
            )
        ''')
        
        # Add legacy data
        cursor.execute('''
            INSERT INTO contacts (linkedin_id, name, company, title, connection_sent)
            VALUES ('legacy123', 'Legacy User', 'OldCorp', 'Manager', CURRENT_TIMESTAMP)
        ''')
        
        legacy_conn.commit()
        
        # Initialize new tracker
        tracker = EnhancedLinkedInTracker(db_path)
        
        # Verify new database structure
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'targets' in tables
        assert 'connections' in tables
        assert 'messages' in tables
        assert 'posts' in tables
        assert 'viral_posts_cache' in tables
        assert 'daily_limits' in tables
        
        conn.close()
        legacy_conn.close()
