#!/bin/bash

# Development runner script for Enterprise Knowledge Assistant

echo "🚀 Starting Enterprise Knowledge Assistant in Development Mode..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Function to cleanup on exit
cleanup() {
    echo -e "\n${RED}Shutting down services...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found. Please run setup.sh first${NC}"
    exit 1
fi

# Load environment variables
source .env

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ OPENAI_API_KEY not set in .env file${NC}"
    echo "Please add your OpenAI API key to the .env file"
    exit 1
fi

echo -e "${BLUE}ℹ️  Starting PostgreSQL with Docker...${NC}"
docker run --name enterprise-kb-postgres -d \
    -e POSTGRES_DB=enterprise_kb \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -p 5432:5432 \
    postgres:15-alpine 2>/dev/null || \
docker start enterprise-kb-postgres 2>/dev/null

# Wait for PostgreSQL to be ready
echo -e "${BLUE}ℹ️  Waiting for PostgreSQL to be ready...${NC}"
sleep 5

# Start backend
echo -e "${BLUE}ℹ️  Starting backend server...${NC}"
cd backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Initialize database
echo -e "${BLUE}ℹ️  Initializing database...${NC}"
python create_tables.py

# Start backend server
echo -e "${GREEN}✅ Starting FastAPI server on http://localhost:8000${NC}"
uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000 &

cd ..

# Start frontend
echo -e "${BLUE}ℹ️  Starting frontend development server...${NC}"
cd frontend

echo -e "${GREEN}✅ Starting React development server on http://localhost:3000${NC}"
npm run dev &

cd ..

echo ""
echo -e "${GREEN}🎉 Enterprise Knowledge Assistant is running!${NC}"
echo ""
echo -e "${BLUE}📝 URLs:${NC}"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo -e "${BLUE}👤 Default Admin Login:${NC}"
echo "  Email: admin@company.com"
echo "  Password: admin123"
echo ""
echo -e "${BLUE}ℹ️  Press Ctrl+C to stop all services${NC}"

# Wait for all background processes
wait