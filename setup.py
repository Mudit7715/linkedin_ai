#!/usr/bin/env python3
"""
Setup script for LinkedIn AI Outreach System
"""
import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is 3.11+"""
    if sys.version_info < (3, 11):
        print("Error: Python 3.11+ is required")
        sys.exit(1)
    print("✓ Python version OK")

def check_chrome_driver():
    """Check if ChromeDriver is installed"""
    if shutil.which("chromedriver"):
        print("✓ ChromeDriver found")
        return True
    else:
        print("✗ ChromeDriver not found")
        print("  Please install ChromeDriver:")
        print("  - macOS: brew install chromedriver")
        print("  - Or download from https://chromedriver.chromium.org/")
        return False

def check_ollama():
    """Check if Ollama is installed and running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✓ Ollama is running")
            models = response.json().get('models', [])
            if models:
                print(f"  Available models: {', '.join([m['name'] for m in models])}")
            else:
                print("  No models found. Run: ollama pull llama2")
            return True
    except:
        pass
    
    print("✗ Ollama not running")
    print("  Please install and start Ollama:")
    print("  - macOS: brew install ollama && ollama serve")
    print("  - Then: ollama pull llama2")
    return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        shutil.copy('.env.example', '.env')
        print("✓ Created .env file")
        print("  Please edit .env and add your LinkedIn credentials")
    else:
        print("✓ .env file exists")

def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling Python dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✓ Dependencies installed")

def create_directories():
    """Create necessary directories"""
    dirs = ['data', 'logs']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
    print("✓ Created data directories")

def run_tests():
    """Run basic tests"""
    print("\nRunning tests...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])
    if result.returncode == 0:
        print("✓ All tests passed")
    else:
        print("✗ Some tests failed")

def main():
    """Main setup function"""
    print("LinkedIn AI Outreach System Setup")
    print("=================================\n")
    
    # Check prerequisites
    check_python_version()
    chrome_ok = check_chrome_driver()
    ollama_ok = check_ollama()
    
    # Setup environment
    create_env_file()
    install_dependencies()
    create_directories()
    
    # Run tests
    run_tests()
    
    print("\n" + "="*50)
    print("Setup Summary:")
    print("="*50)
    
    if chrome_ok and ollama_ok:
        print("✓ All prerequisites met!")
        print("\nNext steps:")
        print("1. Edit .env with your LinkedIn credentials")
        print("2. Start the dashboard: streamlit run ui/dashboard.py")
        print("3. Or run automation: python -m linkedin_ai_outreach")
    else:
        print("✗ Some prerequisites missing")
        print("\nPlease install missing components and run setup again")
    
    # Check for legacy database
    if os.path.exists("../linkedin_tracker.db"):
        print("\n✓ Found legacy job_search.py database")
        print("  Run migration: python -m linkedin_ai_outreach --migrate")

if __name__ == "__main__":
    main()
