#!/bin/bash

echo "================================================"
echo "Fixing Issues and Starting LearnFlow"
echo "================================================"
echo ""

# 1. Stop Docker containers using port 8000
echo "1. Stopping Docker containers..."
cd /Users/jay/Documents/LearnFlow/microservice
docker-compose down 2>/dev/null || true
echo "   ✓ Docker containers stopped"
echo ""

# 2. Kill any process using port 8000
echo "2. Checking port 8000..."
PORT_PID=$(lsof -nP -iTCP:8000 -sTCP:LISTEN -t 2>/dev/null)
if [ -n "$PORT_PID" ]; then
    echo "   Killing process $PORT_PID using port 8000..."
    kill $PORT_PID 2>/dev/null || true
    sleep 2
    echo "   ✓ Port 8000 freed"
else
    echo "   ✓ Port 8000 is free"
fi
echo ""

# 3. Check/fix RDS security group access
echo "3. Checking RDS connectivity from bastion..."
echo "   SSH into bastion and test RDS connection..."
echo ""
ssh -i ~/Downloads/learnflow.pem ec2-user@18.60.47.38 \
  "nc -vz document-mapping.cn2a2uaicp1r.ap-south-2.rds.amazonaws.com 5432" 2>&1 | grep -q "succeeded"

if [ $? -eq 0 ]; then
    echo "   ✓ Bastion can reach RDS"
else
    echo "   ✗ Bastion cannot reach RDS"
    echo ""
    echo "   ACTION REQUIRED:"
    echo "   Go to AWS Console → EC2 → Security Groups"
    echo "   Find your RDS security group and add inbound rule:"
    echo "     Type: PostgreSQL"
    echo "     Port: 5432"
    echo "     Source: Security group of bastion (bastion-sg)"
    echo ""
    read -p "   Press Enter after fixing the security group..."
fi
echo ""

# 4. Restart the application
echo "4. Starting LearnFlow with RDS..."
echo ""
./scripts/start_with_rds.sh

