import pytest
import sqlite3
import os
import tempfile
from datetime import datetime

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enhanced_tracker import EnhancedLinkedInTracker, Target, OutreachStatus

class TestEnhancedTracker:
    @pytest.fixture
    def tracker(self):
        """Create a tracker with temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        tracker = EnhancedLinkedInTracker(db_path)
        yield tracker
        os.unlink(db_path)
    
    def test_add_target(self, tracker):
        """Test adding a new target"""
        target = Target(
            linkedin_id="test123",
            name="John Doe",
            company="Test Corp",
            title="AI Manager",
            email="john@test.com",
            location="India"
        )
        
        target_id = tracker.add_target(target)
        assert target_id is not None
        
        # Try adding duplicate
        duplicate_id = tracker.add_target(target)
        assert duplicate_id is None
    
    def test_update_target_status(self, tracker):
        """Test updating target status"""
        target = Target(
            linkedin_id="test456",
            name="Jane Smith",
            company="AI Corp",
            title="ML Lead"
        )
        
        tracker.add_target(target)
        tracker.update_target_status("test456", OutreachStatus.CONNECTION_SENT.value)
        
        # Verify status was updated
        conn = sqlite3.connect(tracker.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM targets WHERE linkedin_id = ?", ("test456",))
        status = cursor.fetchone()[0]
        conn.close()
        
        assert status == OutreachStatus.CONNECTION_SENT.value
    
    def test_record_connection_sent(self, tracker):
        """Test recording connection sent"""
        target = Target(
            linkedin_id="test789",
            name="Bob Johnson",
            company="Tech Inc",
            title="Director"
        )
        
        tracker.add_target(target)
        success = tracker.record_connection_sent("test789", "Hi Bob!")
        
        assert success == True
        
        # Check daily limit
        for i in range(30):
            tracker.add_target(Target(
                linkedin_id=f"bulk{i}",
                name=f"User {i}",
                company="Company",
                title="Title"
            ))
            tracker.record_connection_sent(f"bulk{i}")
        
        # 31st should fail
        over_limit = tracker.record_connection_sent("test789")
        assert over_limit == False
    
    def test_get_pending_messages(self, tracker):
        """Test getting pending messages"""
        # Add target
        target = Target(
            linkedin_id="pending123",
            name="Alice Wonder",
            company="AI Labs",
            title="Research Lead"
        )
        
        tracker.add_target(target)
        tracker.record_connection_sent("pending123")
        tracker.record_connection_accepted("pending123")
        
        # Should not appear immediately
        pending = tracker.get_pending_messages(hours_delay=5)
        assert len(pending) == 0
        
        # Manually update accepted time to 6 hours ago
        conn = sqlite3.connect(tracker.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE connections 
            SET accepted_at = datetime('now', '-6 hours')
            WHERE target_id = (SELECT id FROM targets WHERE linkedin_id = ?)
        """, ("pending123",))
        conn.commit()
        conn.close()
        
        # Now should appear
        pending = tracker.get_pending_messages(hours_delay=5)
        assert len(pending) == 1
    
    def test_get_analytics(self, tracker):
        """Test analytics calculation"""
        # Add some test data
        for i in range(10):
            target = Target(
                linkedin_id=f"analytics{i}",
                name=f"User {i}",
                company="Company",
                title="Manager" if i < 5 else "Engineer",
                is_hiring_manager=i < 5
            )
            tracker.add_target(target)
            
            if i < 8:
                tracker.record_connection_sent(f"analytics{i}")
            
            if i < 6:
                tracker.record_connection_accepted(f"analytics{i}")
            
            if i < 4:
                tracker.record_message_sent(f"analytics{i}", "Test message")
        
        analytics = tracker.get_analytics()
        
        assert analytics['total_targets'] == 10
        assert analytics['hiring_managers'] == 5
        assert analytics['connections_sent'] == 8
        assert analytics['connections_accepted'] == 6
        assert analytics['messages_sent'] == 4
        assert analytics['acceptance_rate'] == 0.75
        assert analytics['reply_rate'] == 0.0
