#!/usr/bin/env python3
"""
Migration script to import data from job_search.py database
"""
import sqlite3
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enhanced_tracker import EnhancedLinkedInTracker, Target, OutreachStatus

def migrate_from_job_search(old_db_path: str = "linkedin_tracker.db", 
                          new_db_path: str = "linkedin_ai_outreach.db"):
    """Migrate data from job_search.py database to enhanced tracker"""
    
    print(f"Migrating from {old_db_path} to {new_db_path}...")
    
    # Check if old database exists
    if not os.path.exists(old_db_path):
        print(f"Old database {old_db_path} not found. Skipping migration.")
        return
    
    # Initialize new tracker
    tracker = EnhancedLinkedInTracker(new_db_path)
    
    # Connect to old database
    old_conn = sqlite3.connect(old_db_path)
    
    # Read contacts from old database
    contacts_df = pd.read_sql_query("SELECT * FROM contacts", old_conn)
    
    print(f"Found {len(contacts_df)} contacts to migrate")
    
    # Migrate contacts
    migrated = 0
    for _, contact in contacts_df.iterrows():
        # Determine status based on old data
        if contact['message_replied']:
            status = OutreachStatus.MESSAGE_REPLIED.value
        elif contact['message_sent']:
            status = OutreachStatus.MESSAGE_SENT.value
        elif contact['connection_accepted']:
            status = OutreachStatus.CONNECTION_ACCEPTED.value
        elif contact['connection_sent']:
            status = OutreachStatus.CONNECTION_SENT.value
        else:
            status = OutreachStatus.DISCOVERED.value
        
        # Create target
        target = Target(
            linkedin_id=contact['linkedin_id'],
            name=contact['name'],
            company=contact['company'] or "",
            title=contact['title'] or "",
            status=status,
            profile_summary=contact.get('notes', '')
        )
        
        # Add to new database
        target_id = tracker.add_target(target)
        
        if target_id:
            # Record connection if sent
            if contact['connection_sent']:
                tracker.record_connection_sent(contact['linkedin_id'])
                
            # Record acceptance if accepted
            if contact['connection_accepted']:
                tracker.record_connection_accepted(contact['linkedin_id'])
                
            # Record message if sent
            if contact['message_sent']:
                # Get message content from messages table
                messages_df = pd.read_sql_query(
                    "SELECT * FROM messages WHERE contact_id = ?",
                    old_conn,
                    params=(contact['id'],)
                )
                
                if not messages_df.empty:
                    message_content = messages_df.iloc[0]['content']
                    tracker.record_message_sent(
                        contact['linkedin_id'],
                        message_content
                    )
            
            migrated += 1
            print(f"Migrated: {contact['name']} ({contact['company']})")
    
    old_conn.close()
    
    print(f"\nMigration complete! Migrated {migrated} contacts.")
    
    # Show analytics
    analytics = tracker.get_analytics()
    print("\nNew database analytics:")
    print(f"Total targets: {analytics['total_targets']}")
    print(f"Connections sent: {analytics['connections_sent']}")
    print(f"Connections accepted: {analytics['connections_accepted']}")
    print(f"Messages sent: {analytics['messages_sent']}")
    print(f"Messages replied: {analytics['messages_replied']}")

if __name__ == "__main__":
    # Check if job_search.py database exists in parent directory
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    old_db_path = os.path.join(parent_dir, "..", "linkedin_tracker.db")
    
    if os.path.exists(old_db_path):
        migrate_from_job_search(old_db_path)
    else:
        print("No legacy database found. Starting fresh.")
