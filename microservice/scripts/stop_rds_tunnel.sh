#!/bin/bash

# Stop SSH tunnel and FastAPI service

echo "Stopping SSH tunnel to RDS..."

# Find and kill SSH tunnel process
TUNNEL_PID=$(lsof -Pi :15432 -sTCP:LISTEN -t 2>/dev/null)

if [ -n "$TUNNEL_PID" ]; then
    if ps -p $TUNNEL_PID | grep -q ssh; then
        kill $TUNNEL_PID
        echo "✓ SSH tunnel stopped (PID: $TUNNEL_PID)"
    else
        echo "⚠ Process on port 15432 is not an SSH tunnel (PID: $TUNNEL_PID)"
    fi
else
    echo "No SSH tunnel found on port 15432"
fi

# Kill any running uvicorn processes
UVICORN_PIDS=$(pgrep -f "uvicorn app.main:app")
if [ -n "$UVICORN_PIDS" ]; then
    echo "Stopping FastAPI service..."
    kill $UVICORN_PIDS
    echo "✓ FastAPI service stopped"
else
    echo "No running FastAPI service found"
fi

echo "Done."

