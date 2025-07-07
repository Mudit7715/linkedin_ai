#!/usr/bin/env python3
"""
Quick test script to verify all components are working
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all major imports"""
    print("Testing imports...")
    try:
        from core.enhanced_tracker import EnhancedLinkedInTracker
        print("✅ Enhanced tracker import successful")
        
        from core.ollama_connector import OllamaConnector
        print("✅ Ollama connector import successful")
        
        from scrapers.linkedin_scraper import LinkedInScraper
        print("✅ LinkedIn scraper import successful")
        
        from scrapers.viral_post_miner import ViralPostMiner
        print("✅ Viral post miner import successful")
        
        from core.automation_scheduler import AutomationScheduler
        print("✅ Automation scheduler import successful")
        
        from core.post_generator import PostGenerator
        print("✅ Post generator import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("\nTesting database...")
    try:
        from core.enhanced_tracker import EnhancedLinkedInTracker
        tracker = EnhancedLinkedInTracker()
        analytics = tracker.get_analytics()
        print(f"✅ Database working - {analytics['total_targets']} targets found")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_ollama():
    """Test Ollama connection"""
    print("\nTesting Ollama connection...")
    try:
        from core.ollama_connector import OllamaConnector
        ollama = OllamaConnector()
        if ollama.check_health():
            print("✅ Ollama is running")
            models = ollama.list_models()
            print(f"   Available models: {', '.join(models)}")
            return True
        else:
            print("❌ Ollama is not running")
            print("   Run: ollama serve")
            return False
    except Exception as e:
        print(f"❌ Ollama error: {e}")
        return False

def test_config():
    """Test configuration files"""
    print("\nTesting configuration...")
    try:
        import yaml
        with open('config/prompts.yml', 'r') as f:
            config = yaml.safe_load(f)
        print("✅ Prompts configuration loaded")
        print(f"   Target companies: {len(config['target_companies']['global_leaders'])} global, "
              f"{len(config['target_companies']['india_presence'])} India")
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_env():
    """Test environment variables"""
    print("\nTesting environment...")
    try:
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        linkedin_email = os.getenv('LINKEDIN_EMAIL')
        linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        
        if linkedin_email and linkedin_password:
            print("✅ LinkedIn credentials configured")
        else:
            print("⚠️  LinkedIn credentials not set in .env")
            print("   Please update .env with your credentials")
            
        return True
    except Exception as e:
        print(f"❌ Environment error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 LinkedIn AI Outreach System Test")
    print("===================================")
    
    all_passed = True
    
    # Run tests
    all_passed &= test_imports()
    all_passed &= test_database()
    all_passed &= test_ollama()
    all_passed &= test_config()
    all_passed &= test_env()
    
    print("\n===================================")
    if all_passed:
        print("✅ All tests passed!")
        print("\nYou can now:")
        print("1. Run the dashboard: streamlit run ui/dashboard.py")
        print("2. Start automation: python -m core.automation_scheduler")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        
if __name__ == "__main__":
    main()
