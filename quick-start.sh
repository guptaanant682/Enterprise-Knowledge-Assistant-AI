#!/bin/bash

# ============================================================================
# ENTERPRISE KNOWLEDGE ASSISTANT - ONE-COMMAND SETUP
# ============================================================================
# This script will set up everything you need to run the application
# Just run: bash quick-start.sh
# ============================================================================

set -e  # Exit on any error

echo "🚀 Enterprise Knowledge Assistant - Quick Start Setup"
echo "===================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Step 1: Check prerequisites
echo "📋 Step 1: Checking prerequisites..."
echo ""

# Check Docker
if command -v docker &> /dev/null; then
    print_success "Docker is installed"
else
    print_error "Docker is not installed"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null 2>&1; then
    print_success "Docker Compose is installed"
else
    print_error "Docker Compose is not installed"
    echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi

echo ""

# Step 2: Setup environment file
echo "⚙️  Step 2: Setting up environment configuration..."
echo ""

if [ ! -f ".env" ]; then
    print_info "Creating .env file from template..."
    cp .env.example .env
    print_success ".env file created"
    print_warning "IMPORTANT: Edit .env file to add your API keys if you haven't already"
else
    print_info ".env file already exists, skipping..."
fi

echo ""

# Step 3: Create necessary directories
echo "📁 Step 3: Creating necessary directories..."
echo ""

mkdir -p backend/uploads
mkdir -p backend/chroma_db
print_success "Directories created"

echo ""

# Step 4: Build and start Docker containers
echo "🐳 Step 4: Building and starting Docker containers..."
echo ""

print_info "This may take a few minutes on first run..."
docker-compose up -d --build

echo ""

# Step 5: Wait for services to be ready
echo "⏳ Step 5: Waiting for services to start..."
echo ""

print_info "Waiting for PostgreSQL..."
sleep 5

print_info "Waiting for backend to initialize..."
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    print_success "All services are running!"
else
    print_error "Some services failed to start"
    docker-compose logs
    exit 1
fi

echo ""

# Step 6: Display success message and next steps
echo "=============================================="
echo "🎉 Setup Complete!"
echo "=============================================="
echo ""
print_success "Your Enterprise Knowledge Assistant is now running!"
echo ""
echo "📌 Access your application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Next Steps:"
echo "   1. Open .env file and verify your AI API keys are configured"
echo "   2. Visit http://localhost:3000 to access the application"
echo "   3. Register a new account or login with Google OAuth"
echo "   4. Start uploading documents and asking questions!"
echo ""
echo "🔧 Useful Commands:"
echo "   View logs:        docker-compose logs -f"
echo "   Stop services:    docker-compose down"
echo "   Restart:          docker-compose restart"
echo "   Reset database:   docker-compose down -v && docker-compose up -d"
echo ""
echo "📚 Documentation:"
echo "   Check README.md for detailed setup instructions"
echo ""
echo "⚙️  Configured AI Providers (cascade fallback):"
echo "   Priority 1: OpenAI GPT-4"
echo "   Priority 2: Anthropic Claude 3.5 Sonnet"
echo "   Priority 3: OpenRouter (GPT-4 or Claude)"
echo "   Priority 4: Groq (Llama 70B)"
echo ""
print_warning "Note: At least ONE AI provider API key must be configured in .env"
echo ""
echo "=============================================="

# Optional: Open browser
if command -v xdg-open &> /dev/null; then
    read -p "Would you like to open the application in your browser? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xdg-open http://localhost:3000
    fi
elif command -v open &> /dev/null; then
    read -p "Would you like to open the application in your browser? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open http://localhost:3000
    fi
fi
