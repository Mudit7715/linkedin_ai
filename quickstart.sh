#!/bin/bash

# LinkedIn AI Outreach Quick Start
# This script quickly starts the system with minimal setup

set -e

echo "🚀 LinkedIn AI Outreach Quick Start"
echo "==================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo ""
    echo "📝 Please edit .env file with your LinkedIn credentials:"
    echo "   LINKEDIN_EMAIL=your_email@example.com"
    echo "   LINKEDIN_PASSWORD=your_password"
    echo ""
    read -p "Press Enter after updating .env file..."
fi

# Check if Ollama is running
echo ""
echo "Checking Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Starting Ollama..."
    if command -v ollama &> /dev/null; then
        ollama serve &
        sleep 5
        
        # Pull llama2 if not present
        if ! ollama list | grep -q "llama2"; then
            echo "Downloading llama2 model (this may take a few minutes)..."
            ollama pull llama2
        fi
    else
        echo "❌ Ollama not installed. Please install it first:"
        echo "   macOS: brew install ollama"
        echo "   Linux: curl -fsSL https://ollama.ai/install.sh | sh"
        exit 1
    fi
fi

# Create necessary directories
mkdir -p data logs

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if ! pip show streamlit > /dev/null 2>&1; then
    echo ""
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Initialize database
echo ""
echo "Initializing database..."
python3 -c "from core.enhanced_tracker import EnhancedLinkedInTracker; EnhancedLinkedInTracker()" 2>/dev/null || true

# Start the dashboard
echo ""
echo "==================================="
echo "✅ System ready!"
echo "==================================="
echo ""
echo "Starting dashboard on http://localhost:8501"
echo ""
echo "In the dashboard you can:"
echo "  📊 View analytics and metrics"
echo "  🎯 Manage your outreach pipeline"
echo "  📝 Edit AI prompts"
echo "  🔥 Generate viral posts"
echo "  ⚙️ Configure settings"
echo ""
echo "To start automation, run in another terminal:"
echo "  python -m linkedin_ai_outreach.core.automation_scheduler"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the dashboard
streamlit run ui/dashboard.py
