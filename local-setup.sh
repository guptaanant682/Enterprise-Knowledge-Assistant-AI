#!/bin/bash

# ============================================================================
# ENTERPRISE KNOWLEDGE ASSISTANT - LOCAL SETUP (NO DOCKER)
# ============================================================================
# This script sets up the application for local development without Docker
# Run: bash local-setup.sh
# ============================================================================

set -e  # Exit on any error

echo "🚀 Enterprise Knowledge Assistant - Local Setup"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

# Step 1: Check prerequisites
echo "📋 Step 1: Checking prerequisites..."
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python is installed: $PYTHON_VERSION"
else
    print_error "Python 3 is not installed"
    echo "Please install Python 3.9+ from: https://www.python.org/downloads/"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js is installed: $NODE_VERSION"
else
    print_error "Node.js is not installed"
    echo "Please install Node.js from: https://nodejs.org/"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    print_success "npm is installed: v$NPM_VERSION"
else
    print_error "npm is not installed"
    exit 1
fi

# Check PostgreSQL
if command -v psql &> /dev/null; then
    print_success "PostgreSQL client is installed"
    HAS_POSTGRES=true
else
    print_warning "PostgreSQL not found - we'll use Docker for database only"
    HAS_POSTGRES=false

    # Check if Docker is available for database
    if ! command -v docker &> /dev/null; then
        print_error "Neither PostgreSQL nor Docker is installed"
        echo "Please install one of:"
        echo "  1. PostgreSQL: https://www.postgresql.org/download/"
        echo "  2. Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
fi

echo ""

# Step 2: Setup environment file
echo "⚙️  Step 2: Setting up environment configuration..."
echo ""

if [ ! -f ".env" ]; then
    print_info "Creating .env file from template..."
    cp .env.example .env

    # Update .env for local development
    if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Update DATABASE_URL for local PostgreSQL
        if [ "$HAS_POSTGRES" = true ]; then
            sed -i.bak 's|DATABASE_URL=postgresql://postgres:postgres@postgres:5432/enterprise_kb|DATABASE_URL=postgresql://postgres:postgres@localhost:5432/enterprise_kb|' .env
            rm .env.bak
            print_info "Updated DATABASE_URL for local PostgreSQL"
        fi
    fi

    print_success ".env file created"
else
    print_info ".env file already exists"
fi

echo ""

# Step 3: Setup Database
echo "🗄️  Step 3: Setting up PostgreSQL database..."
echo ""

if [ "$HAS_POSTGRES" = true ]; then
    print_info "Using local PostgreSQL installation"

    # Create database
    print_info "Creating database 'enterprise_kb'..."

    # Try to create database (may fail if already exists, that's ok)
    psql -U postgres -c "CREATE DATABASE enterprise_kb;" 2>/dev/null && print_success "Database created" || print_warning "Database may already exist"

else
    print_info "Starting PostgreSQL in Docker..."

    # Check if postgres container is running
    if docker ps | grep -q postgres_local; then
        print_info "PostgreSQL container already running"
    else
        # Run PostgreSQL in Docker
        docker run -d \
            --name postgres_local \
            -e POSTGRES_PASSWORD=postgres \
            -e POSTGRES_DB=enterprise_kb \
            -p 5432:5432 \
            postgres:15-alpine

        print_success "PostgreSQL started in Docker"
        print_info "Waiting for PostgreSQL to be ready..."
        sleep 5
    fi
fi

echo ""

# Step 4: Setup Python Backend
echo "🐍 Step 4: Setting up Python backend..."
echo ""

cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
print_info "Installing Python dependencies (this may take a few minutes)..."
pip install -r requirements.txt --quiet

print_success "Python dependencies installed"

# Create necessary directories
mkdir -p uploads chroma_db
print_success "Created uploads and chroma_db directories"

echo ""

# Step 5: Initialize Database
echo "🔧 Step 5: Initializing database tables..."
echo ""

if [ -f "create_tables.py" ]; then
    python create_tables.py
    print_success "Database tables created"
else
    print_warning "create_tables.py not found - you may need to run migrations manually"
fi

echo ""
cd ..

# Step 6: Setup React Frontend
echo "⚛️  Step 6: Setting up React frontend..."
echo ""

cd frontend

# Install dependencies
print_info "Installing Node.js dependencies (this may take a few minutes)..."
npm install

print_success "Node.js dependencies installed"

# Create frontend .env if it doesn't exist
if [ ! -f ".env" ]; then
    cat > .env << EOF
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=188963818469-rhgjq4jhop8u3eaaqjnv6ndkk1hgpb1u.apps.googleusercontent.com
EOF
    print_success "Frontend .env created"
fi

cd ..

echo ""

# Step 7: Final Instructions
echo "=============================================="
echo "🎉 Local Setup Complete!"
echo "=============================================="
echo ""
print_success "Your Enterprise Knowledge Assistant is ready for local development!"
echo ""
echo "📝 To start the application:"
echo ""
echo "   Terminal 1 (Backend):"
echo "   ${GREEN}cd backend${NC}"
echo "   ${GREEN}source venv/bin/activate${NC}  # On Windows: venv\\Scripts\\activate"
echo "   ${GREEN}uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000${NC}"
echo ""
echo "   Terminal 2 (Frontend):"
echo "   ${GREEN}cd frontend${NC}"
echo "   ${GREEN}npm run dev${NC}"
echo ""
echo "   The app will open at: ${BLUE}http://localhost:3000${NC}"
echo "   Backend API docs: ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo "🔧 Useful Commands:"
echo ""
echo "   Start backend:"
echo "   ${GREEN}cd backend && source venv/bin/activate && uvicorn main:socket_app --reload${NC}"
echo ""
echo "   Start frontend:"
echo "   ${GREEN}cd frontend && npm run dev${NC}"
echo ""
echo "   Stop PostgreSQL (if using Docker):"
echo "   ${GREEN}docker stop postgres_local${NC}"
echo ""
echo "   View backend logs:"
echo "   ${GREEN}tail -f backend/app.log${NC}"
echo ""
echo "⚙️  Configuration:"
echo "   - Edit ${BLUE}.env${NC} for API keys and settings"
echo "   - Backend runs on port 8000"
echo "   - Frontend runs on port 3000 (auto-opens browser)"
echo ""
echo "📚 Next Steps:"
echo "   1. Verify your AI API keys in .env"
echo "   2. Start backend in one terminal"
echo "   3. Start frontend in another terminal"
echo "   4. Visit http://localhost:3000"
echo "   5. Register an account and start using!"
echo ""
echo "=============================================="

# Optional: Offer to start services
echo ""
read -p "Would you like to start both services now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Starting services..."
    echo ""

    # Start backend in background
    cd backend
    source venv/bin/activate
    print_step "Starting backend on http://localhost:8000..."
    uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..

    sleep 3

    # Start frontend in background
    cd frontend
    print_step "Starting frontend on http://localhost:3000..."
    npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..

    sleep 5

    echo ""
    print_success "Services started!"
    echo ""
    echo "Backend PID: $BACKEND_PID (logs: backend/backend.log)"
    echo "Frontend PID: $FRONTEND_PID (logs: frontend/frontend.log)"
    echo ""
    echo "To stop services:"
    echo "  kill $BACKEND_PID $FRONTEND_PID"
    echo ""

    # Try to open browser
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:3000
    elif command -v open &> /dev/null; then
        open http://localhost:3000
    fi
else
    print_info "You can start services manually using the commands above"
fi

echo ""
print_success "Happy coding! 🚀"
