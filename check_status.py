#!/usr/bin/env python3
"""
Diagnostic script to check project completeness
"""
import os
import sys
import importlib.util

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - Missing!")
        return False

def check_module_imports(module_path, description):
    """Check if a Python module can be imported"""
    try:
        spec = importlib.util.spec_from_file_location("test_module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"✅ {description} - Imports OK")
        return True
    except Exception as e:
        print(f"❌ {description} - Import error: {str(e)[:50]}...")
        return False

def main():
    print("LinkedIn AI Outreach System - Status Check")
    print("==========================================\n")
    
    all_good = True
    
    # Check directory structure
    print("1. Directory Structure:")
    dirs = ['config', 'core', 'scrapers', 'ui', 'tests', 'data', 'logs']
    for dir_name in dirs:
        if not check_file_exists(dir_name, f"Directory: {dir_name}"):
            all_good = False
    
    # Check configuration files
    print("\n2. Configuration Files:")
    config_files = [
        ('.env.example', 'Environment template'),
        ('config/prompts.yml', 'Prompts configuration'),
        ('requirements.txt', 'Python dependencies'),
        ('README.md', 'Documentation'),
        ('Dockerfile', 'Docker configuration'),
        ('docker-compose.yml', 'Docker Compose'),
        ('.gitignore', 'Git ignore file')
    ]
    
    for filepath, desc in config_files:
        if not check_file_exists(filepath, desc):
            all_good = False
    
    # Check core modules
    print("\n3. Core Modules:")
    core_modules = [
        ('core/enhanced_tracker.py', 'Enhanced Tracker'),
        ('core/ollama_connector.py', 'Ollama Connector'),
        ('core/automation_scheduler.py', 'Automation Scheduler'),
        ('core/post_generator.py', 'Post Generator'),
        ('core/migrate_job_search.py', 'Migration Script')
    ]
    
    for filepath, desc in core_modules:
        if check_file_exists(filepath, f"{desc} exists"):
            if not check_module_imports(filepath, f"{desc} imports"):
                all_good = False
        else:
            all_good = False
    
    # Check scrapers
    print("\n4. Scraper Modules:")
    scraper_modules = [
        ('scrapers/linkedin_scraper.py', 'LinkedIn Scraper'),
        ('scrapers/viral_post_miner.py', 'Viral Post Miner')
    ]
    
    for filepath, desc in scraper_modules:
        if check_file_exists(filepath, f"{desc} exists"):
            if not check_module_imports(filepath, f"{desc} imports"):
                all_good = False
        else:
            all_good = False
    
    # Check UI
    print("\n5. UI Module:")
    if check_file_exists('ui/dashboard.py', 'Dashboard exists'):
        if not check_module_imports('ui/dashboard.py', 'Dashboard imports'):
            all_good = False
    else:
        all_good = False
    
    # Check tests
    print("\n6. Test Suite:")
    test_files = [
        ('tests/test_enhanced_tracker.py', 'Tracker tests'),
        ('tests/test_ollama_connector.py', 'Ollama tests'),
        ('tests/test_integration.py', 'Integration tests')
    ]
    
    for filepath, desc in test_files:
        if not check_file_exists(filepath, desc):
            all_good = False
    
    # Check executables
    print("\n7. Executable Scripts:")
    exec_files = [
        ('setup.py', 'Setup script'),
        ('run.sh', 'Run script'),
        ('__main__.py', 'Main module')
    ]
    
    for filepath, desc in exec_files:
        if not check_file_exists(filepath, desc):
            all_good = False
    
    # Summary
    print("\n" + "="*50)
    if all_good:
        print("✅ All components are present!")
        print("\nNext steps:")
        print("1. Run: python setup.py")
        print("2. Configure .env file")
        print("3. Start Ollama: ollama serve")
        print("4. Run: ./run.sh")
    else:
        print("❌ Some components are missing or have errors.")
        print("\nPlease check the errors above and fix them.")
    
    # Check for job_search.py in parent directory
    print("\n" + "="*50)
    print("Legacy Database Check:")
    if os.path.exists("../job_search.py"):
        print("✅ Found job_search.py in parent directory")
        if os.path.exists("../linkedin_tracker.db"):
            print("✅ Found legacy database")
            print("   Run migration: python -m linkedin_ai_outreach --migrate")
        else:
            print("ℹ️  No legacy database found")
    else:
        print("ℹ️  No job_search.py found in parent directory")

if __name__ == "__main__":
    main()
