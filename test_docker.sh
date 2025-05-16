#!/bin/bash
# Test script for Docker deployment

set -e  # Exit on error

# Bold text function
bold() {
  echo -e "\033[1m$1\033[0m"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Please install Docker first."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "Docker daemon is not running. Please start Docker first."
    exit 1
fi

bold "Building and starting Docker containers..."

# Build and start the containers
docker-compose build
docker-compose up -d

echo
bold "Docker containers started successfully!"
echo "The dashboard should be available at http://localhost:8501"
echo

# Show running containers
bold "Running containers:"
docker-compose ps

echo
bold "Container logs:"
docker-compose logs --tail=10

echo
bold "To stop the containers, run:"
echo "docker-compose down" 