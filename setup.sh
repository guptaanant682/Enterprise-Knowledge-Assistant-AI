#!/bin/bash

# Enterprise Knowledge Assistant Setup Script

set -e

echo "🚀 Setting up Enterprise Knowledge Assistant..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

print_status "Prerequisites check passed!"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_info "Creating .env file from template..."
    cp .env.example .env
    print_warning "Please edit .env file with your API keys and configuration"
    print_info "At minimum, you need to set OPENAI_API_KEY"
fi

# Setup backend
print_info "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file for backend
if [ ! -f .env ]; then
    cp .env.example .env
    print_warning "Please edit backend/.env with your configuration"
fi

cd ..

# Setup frontend
print_info "Setting up frontend..."
cd frontend

# Install Node.js dependencies
print_info "Installing Node.js dependencies..."
npm install

cd ..

print_status "Setup completed!"

echo ""
print_info "Next steps:"
echo "1. Edit .env files with your API keys"
echo "2. Start the services:"
echo "   Option A - Using Docker Compose (Recommended):"
echo "     docker-compose up -d"
echo ""
echo "   Option B - Manual setup:"
echo "     a. Start PostgreSQL database"
echo "     b. Run backend: cd backend && source venv/bin/activate && python create_tables.py && uvicorn main:socket_app --reload"
echo "     c. Run frontend: cd frontend && npm run dev"
echo ""
echo "3. Access the application at http://localhost:3000"
echo "4. Login as admin (admin@company.com / admin123) and upload documents"

print_warning "Remember to change the default admin password!"

echo ""
print_status "Enterprise Knowledge Assistant setup complete! 🎉"