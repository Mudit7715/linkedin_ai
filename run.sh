#!/bin/bash

# LinkedIn AI Outreach System Runner

echo "LinkedIn AI Outreach System"
echo "=========================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and add your credentials"
    exit 1
fi

# Menu
echo "What would you like to do?"
echo "1) Run setup"
echo "2) Start dashboard (UI)"
echo "3) Start automation (background)"
echo "4) Run both (dashboard + automation)"
echo "5) Run with Docker"
echo "6) Run tests"
echo "7) Migrate from job_search.py"
echo ""

read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        echo "Running setup..."
        python setup.py
        ;;
    2)
        echo "Starting dashboard..."
        streamlit run ui/dashboard.py
        ;;
    3)
        echo "Starting automation..."
        python -m linkedin_ai_outreach
        ;;
    4)
        echo "Starting both services..."
        # Start automation in background
        python -m linkedin_ai_outreach &
        AUTOMATION_PID=$!
        echo "Automation started (PID: $AUTOMATION_PID)"
        
        # Start dashboard
        streamlit run ui/dashboard.py
        
        # Kill automation when dashboard exits
        kill $AUTOMATION_PID
        ;;
    5)
        echo "Starting with Docker..."
        docker-compose up -d
        echo ""
        echo "Services started!"
        echo "Dashboard: http://localhost:8501"
        echo ""
        echo "To view logs: docker-compose logs -f"
        echo "To stop: docker-compose down"
        ;;
    6)
        echo "Running tests..."
        pytest tests/ -v
        ;;
    7)
        echo "Running migration..."
        python -m linkedin_ai_outreach --migrate
        ;;
    *)
        echo "Invalid choice!"
        exit 1
        ;;
esac
