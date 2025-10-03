#!/usr/bin/env python3
"""
Test script to verify Enterprise Knowledge Assistant setup
"""

import sys
import os
import requests
import time
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_status(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.NC}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.NC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.NC}")

def test_backend_health():
    """Test if backend is running and healthy"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print_status("Backend is running and healthy")
            return True
        else:
            print_error(f"Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend at http://localhost:8000")
        return False
    except Exception as e:
        print_error(f"Backend health check error: {e}")
        return False

def test_frontend():
    """Test if frontend is accessible"""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print_status("Frontend is accessible")
            return True
        else:
            print_error(f"Frontend check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to frontend at http://localhost:3000")
        return False
    except Exception as e:
        print_error(f"Frontend check error: {e}")
        return False

def test_api_endpoints():
    """Test key API endpoints"""
    endpoints = [
        "/",
        "/docs",
        "/api/auth/login"
    ]
    
    base_url = "http://localhost:8000"
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code in [200, 422]:  # 422 is expected for login without data
                print_status(f"API endpoint {endpoint} is accessible")
            else:
                print_warning(f"API endpoint {endpoint} returned {response.status_code}")
        except Exception as e:
            print_error(f"API endpoint {endpoint} failed: {e}")

def check_environment():
    """Check environment configuration"""
    env_file = Path(".env")
    
    if env_file.exists():
        print_status(".env file exists")
        
        # Check for required variables
        with open(env_file, 'r') as f:
            content = f.read()
            
        if "OPENAI_API_KEY" in content and "your-openai-api-key" not in content:
            print_status("OpenAI API key is configured")
        else:
            print_warning("OpenAI API key needs to be configured in .env")
            
        if "GOOGLE_CLIENT_ID" in content and "your-google-client-id" not in content:
            print_status("Google OAuth is configured")
        else:
            print_info("Google OAuth is not configured (optional)")
    else:
        print_warning(".env file not found")

def check_file_structure():
    """Check if all required files exist"""
    required_files = [
        "backend/main.py",
        "backend/requirements.txt",
        "frontend/package.json",
        "frontend/src/App.jsx",
        "docker-compose.yml",
        "README.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print_status(f"Found {file_path}")
    
    if missing_files:
        print_error(f"Missing files: {', '.join(missing_files)}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🧪 Testing Enterprise Knowledge Assistant Setup")
    print("=" * 60)
    
    # Check file structure
    print_info("Checking file structure...")
    if not check_file_structure():
        print_error("File structure check failed")
        return False
    
    # Check environment
    print_info("Checking environment configuration...")
    check_environment()
    
    # Test services
    print_info("Testing services...")
    
    backend_ok = test_backend_health()
    frontend_ok = test_frontend()
    
    if backend_ok:
        print_info("Testing API endpoints...")
        test_api_endpoints()
    else:
        print_warning("Skipping API tests - backend not running")
        print_info("To start backend: cd backend && uvicorn main:socket_app --reload")
    
    if not frontend_ok:
        print_warning("Frontend not accessible")
        print_info("To start frontend: cd frontend && npm run dev")
    
    # Summary
    print("\n" + "=" * 60)
    
    if backend_ok and frontend_ok:
        print_status("All systems are running! 🎉")
        print_info("You can access the application at:")
        print_info("  Frontend: http://localhost:3000")
        print_info("  Backend API: http://localhost:8000")
        print_info("  API Documentation: http://localhost:8000/docs")
        print_info("\nDefault admin login:")
        print_info("  Email: admin@company.com")
        print_info("  Password: admin123")
    else:
        print_warning("Some services are not running")
        print_info("Run './run-dev.sh' to start all services")

if __name__ == "__main__":
    main()