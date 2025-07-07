#!/bin/bash

# LinkedIn AI Outreach System Setup Script
# This script sets up the complete system on macOS/Linux

set -e  # Exit on error

echo "🤖 LinkedIn AI Outreach System Setup"
echo "===================================="

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo "❌ Error: Python 3.11+ is required. Current version: $python_version"
    exit 1
fi
echo "✅ Python $python_version detected"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Check for Ollama
echo ""
echo "Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is installed"
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is running"
    else
        echo "⚠️  Ollama is not running. Starting Ollama..."
        ollama serve &
        sleep 5
    fi
    
    # Check for models
    echo "Checking for LLM models..."
    if ollama list | grep -q "llama2"; then
        echo "✅ llama2 model found"
    else
        echo "📥 Downloading llama2 model..."
        ollama pull llama2
    fi
else
    echo "❌ Ollama not found. Please install Ollama:"
    echo "   macOS: brew install ollama"
    echo "   Linux: curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

# Check for ChromeDriver
echo ""
echo "Checking ChromeDriver..."
if command -v chromedriver &> /dev/null; then
    echo "✅ ChromeDriver is installed"
else
    echo "⚠️  ChromeDriver not found"
    echo "   macOS: brew install chromedriver"
    echo "   Linux: Download from https://chromedriver.chromium.org/"
fi

# Create necessary directories
echo ""
echo "Creating project directories..."
mkdir -p data
mkdir -p logs
echo "✅ Directories created"

# Setup environment file
echo ""
if [ ! -f ".env" ]; then
    echo "Setting up environment file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your LinkedIn credentials"
else
    echo "✅ Environment file exists"
fi

# Initialize database
echo ""
echo "Initializing database..."
python3 -c "from core.enhanced_tracker import EnhancedLinkedInTracker; EnhancedLinkedInTracker()"
echo "✅ Database initialized"

# Check for job_search.py migration
echo ""
echo "Checking for legacy job_search.py data..."
if [ -f "../job_search.py" ] && [ -f "../linkedin_tracker.db" ]; then
    echo "Found legacy data. Migrating..."
    python3 -m core.migrate_job_search
else
    echo "✅ No legacy data to migrate"
fi

# Final instructions
echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your LinkedIn credentials"
echo "2. Start the dashboard: streamlit run ui/dashboard.py"
echo "3. Start the scheduler: python -m core.automation_scheduler"
echo ""
echo "Quick Start Commands:"
echo "  📊 Dashboard:  streamlit run ui/dashboard.py"
echo "  🤖 Scheduler:  python -m core.automation_scheduler"
echo "  🧪 Run tests:  pytest tests/"
echo "  📖 View docs:  open README.md"
echo ""
echo "Happy automating! 🚀"
