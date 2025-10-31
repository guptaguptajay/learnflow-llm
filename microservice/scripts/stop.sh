#!/bin/bash

# Stop script for GenAI Document Mapping Service

set -e

echo "=================================="
echo "Stopping GenAI Document Mapping Service"
echo "=================================="

docker-compose down

echo ""
echo "Services stopped successfully!"
echo ""
echo "To remove all data volumes, run:"
echo "  docker-compose down -v"
echo ""

