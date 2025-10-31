#!/bin/bash

# Start script for GenAI Document Mapping Service with RDS connection
# This script manages the SSH tunnel to RDS and starts the FastAPI service

set -e

echo "================================================"
echo "GenAI Document Mapping Service - RDS Setup"
echo "================================================"

# Configuration
BASTION_IP="18.60.47.38"
PEM_FILE="$HOME/Downloads/learnflow.pem"
RDS_ENDPOINT="document-mapping.cn2a2uaicp1r.ap-south-2.rds.amazonaws.com"
LOCAL_PORT=15432
RDS_PORT=5432

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if PEM file exists
if [ ! -f "$PEM_FILE" ]; then
    echo -e "${RED}Error: PEM file not found at $PEM_FILE${NC}"
    echo "Please ensure your learnflow.pem file is in ~/Downloads/"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo ""
    echo "Please create .env file with the following content:"
    echo ""
    echo "database_url=postgresql+psycopg://postgres:Learnflow123@127.0.0.1:15432/document-mapping"
    echo "openai_api_key=YOUR_OPENAI_API_KEY"
    echo "postgres_host=127.0.0.1"
    echo "postgres_port=15432"
    echo "postgres_db=document-mapping"
    echo "postgres_user=postgres"
    echo "postgres_password=Learnflow123"
    echo ""
    exit 1
fi

# Check if local port is already in use
if lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Port $LOCAL_PORT is already in use${NC}"
    echo "Checking if it's our SSH tunnel..."
    
    PID=$(lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t)
    if ps -p $PID | grep -q ssh; then
        echo -e "${GREEN}✓ SSH tunnel already running (PID: $PID)${NC}"
        TUNNEL_RUNNING=true
    else
        echo -e "${RED}Error: Port $LOCAL_PORT is in use by another process (PID: $PID)${NC}"
        echo "Please stop that process or use a different port."
        exit 1
    fi
else
    TUNNEL_RUNNING=false
fi

# Start SSH tunnel if not running
if [ "$TUNNEL_RUNNING" = false ]; then
    echo ""
    echo "Starting SSH tunnel to RDS..."
    echo "  Bastion: $BASTION_IP"
    echo "  RDS: $RDS_ENDPOINT:$RDS_PORT"
    echo "  Local: 127.0.0.1:$LOCAL_PORT"
    
    # Start tunnel in background
    ssh -f -N -i "$PEM_FILE" \
        -L $LOCAL_PORT:$RDS_ENDPOINT:$RDS_PORT \
        ec2-user@$BASTION_IP \
        -o StrictHostKeyChecking=no \
        -o ServerAliveInterval=60 \
        -o ServerAliveCountMax=3
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ SSH tunnel started successfully${NC}"
        sleep 2
    else
        echo -e "${RED}✗ Failed to start SSH tunnel${NC}"
        exit 1
    fi
fi

# Test database connection
echo ""
echo "Testing database connection..."
if command -v psql &> /dev/null; then
    if psql "host=127.0.0.1 dbname=document-mapping user=postgres password=Learnflow123 port=$LOCAL_PORT sslmode=disable" -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database connection successful${NC}"
    else
        echo -e "${RED}✗ Database connection failed${NC}"
        echo "Please verify:"
        echo "  - SSH tunnel is working"
        echo "  - RDS security group allows bastion access"
        echo "  - Database credentials are correct"
    fi
else
    echo -e "${YELLOW}⚠ psql not found, skipping connection test${NC}"
fi

# Check Python and dependencies
echo ""
echo "Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found!${NC}"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing/updating dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Start the FastAPI application
echo ""
echo "================================================"
echo "Starting FastAPI Application"
echo "================================================"
echo ""
echo -e "${GREEN}Application will be available at:${NC}"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Health Check: http://localhost:8000/health"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the application${NC}"
echo ""

# Run the application
cd /Users/jay/Documents/LearnFlow/microservice
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Cleanup on exit is handled by trap or manual stop

