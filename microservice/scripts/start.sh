#!/bin/bash

# Quick start script for GenAI Document Mapping Service

set -e

echo "=================================="
echo "GenAI Document Mapping Service"
echo "Quick Start Script"
echo "=================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose not found!"
    echo "Please install docker-compose."
    exit 1
fi

echo ""
echo "Starting services..."
echo ""

# Start services
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo ""
echo "Checking service health..."

# Check PostgreSQL
if docker-compose ps postgres | grep -q "healthy"; then
    echo "✓ PostgreSQL is healthy"
else
    echo "✗ PostgreSQL is not healthy"
fi

# Check Qdrant
if docker-compose ps qdrant | grep -q "healthy"; then
    echo "✓ Qdrant is healthy"
else
    echo "✗ Qdrant is not healthy"
fi

# Check API
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API is healthy"
else
    echo "✗ API is not healthy"
fi

echo ""
echo "=================================="
echo "Services started successfully!"
echo "=================================="
echo ""
echo "Access the API:"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/health"
echo "  - Qdrant Dashboard: http://localhost:6333/dashboard"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f api"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""

