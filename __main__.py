#!/usr/bin/env python3
"""
Main entry point for LinkedIn AI Outreach System
"""
import sys
import argparse
import logging
from dotenv import load_dotenv

from core.automation_scheduler import AutomationScheduler
from core.migrate_job_search import migrate_from_job_search

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='LinkedIn AI Outreach Automation')
    parser.add_argument(
        '--migrate',
        action='store_true',
        help='Migrate data from job_search.py database'
    )
    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Run all jobs once and exit'
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    if args.migrate:
        logger.info("Running migration from job_search.py...")
        migrate_from_job_search()
        return
    
    # Initialize scheduler
    scheduler = AutomationScheduler()
    
    if args.run_once:
        logger.info("Running all jobs once...")
        scheduler.run_nightly_scraper()
        scheduler.run_morning_viral_post_job()
        scheduler.run_connection_requests()
        scheduler.check_accepted_connections()
        logger.info("All jobs completed!")
    else:
        try:
            logger.info("Starting automation scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping automation scheduler...")
            scheduler.stop()

if __name__ == "__main__":
    main()
