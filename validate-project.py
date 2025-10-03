#!/usr/bin/env python3
"""
Project validation script for Enterprise Knowledge Assistant
Checks for syntax errors, missing imports, and common issues
"""

import os
import sys
import ast
import json
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def print_status(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.NC}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.NC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.NC}")

def validate_python_file(file_path):
    """Validate Python file syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Check syntax
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def validate_json_file(file_path):
    """Validate JSON file syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True, None
    except json.JSONDecodeError as e:
        return False, f"JSON error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        # Backend files
        "backend/main.py",
        "backend/config.py",
        "backend/database.py",
        "backend/models.py",
        "backend/schemas.py",
        "backend/auth_utils.py",
        "backend/requirements.txt",
        
        # Backend routers
        "backend/routers/__init__.py",
        "backend/routers/auth.py",
        "backend/routers/chat.py",
        "backend/routers/knowledge.py",
        "backend/routers/dashboard.py",
        "backend/routers/admin.py",
        
        # Backend services
        "backend/services/__init__.py",
        "backend/services/ai_service.py",
        "backend/services/knowledge_service.py",
        "backend/services/file_service.py",
        
        # Frontend files
        "frontend/package.json",
        "frontend/vite.config.js",
        "frontend/tailwind.config.js",
        "frontend/src/main.jsx",
        "frontend/src/App.jsx",
        "frontend/src/index.css",
        
        # Frontend components
        "frontend/src/components/Navbar.jsx",
        
        # Frontend contexts
        "frontend/src/contexts/AuthContext.jsx",
        "frontend/src/contexts/SocketContext.jsx",
        
        # Frontend pages
        "frontend/src/pages/Login.jsx",
        "frontend/src/pages/Dashboard.jsx",
        "frontend/src/pages/Chat.jsx",
        "frontend/src/pages/KnowledgeBase.jsx",
        "frontend/src/pages/Admin.jsx",
        
        # Configuration files
        "docker-compose.yml",
        "setup.sh",
        "run-dev.sh",
        "README.md",
        ".env.example",
        ".gitignore",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    return missing_files

def check_python_imports():
    """Check for common import issues in Python files"""
    python_files = []
    for root, dirs, files in os.walk("backend"):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    issues = []
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for common issues
            if "from database import Base" in content and "models.py" in file_path:
                issues.append(f"{file_path}: Potential circular import with Base")
            
            if "import openai" in content and "openai.ChatCompletion" in content:
                issues.append(f"{file_path}: Using deprecated OpenAI API syntax")
            
            if "PyPDF2" in content:
                issues.append(f"{file_path}: Using deprecated PyPDF2 import")
                
        except Exception as e:
            issues.append(f"{file_path}: Error reading file - {e}")
    
    return issues

def validate_package_json():
    """Validate frontend package.json"""
    package_json_path = "frontend/package.json"
    if not Path(package_json_path).exists():
        return False, "package.json not found"
    
    is_valid, error = validate_json_file(package_json_path)
    if not is_valid:
        return False, error
    
    # Check for required dependencies
    with open(package_json_path, 'r') as f:
        package_data = json.load(f)
    
    required_deps = [
        "react", "react-dom", "react-router-dom", 
        "axios", "socket.io-client", "lucide-react"
    ]
    
    dependencies = package_data.get("dependencies", {})
    missing_deps = [dep for dep in required_deps if dep not in dependencies]
    
    if missing_deps:
        return False, f"Missing dependencies: {', '.join(missing_deps)}"
    
    return True, None

def main():
    """Main validation function"""
    print("🔍 Validating Enterprise Knowledge Assistant Project")
    print("=" * 60)
    
    total_issues = 0
    
    # Check required files
    print_info("Checking required files...")
    missing_files = check_required_files()
    if missing_files:
        print_error(f"Missing files ({len(missing_files)}):")
        for file in missing_files:
            print(f"   - {file}")
        total_issues += len(missing_files)
    else:
        print_status("All required files present")
    
    # Validate Python files
    print_info("Validating Python syntax...")
    python_files = []
    for root, dirs, files in os.walk("backend"):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    python_errors = 0
    for file_path in python_files:
        is_valid, error = validate_python_file(file_path)
        if not is_valid:
            print_error(f"{file_path}: {error}")
            python_errors += 1
    
    if python_errors == 0:
        print_status(f"All Python files ({len(python_files)}) have valid syntax")
    else:
        total_issues += python_errors
    
    # Check Python imports
    print_info("Checking Python imports...")
    import_issues = check_python_imports()
    if import_issues:
        print_warning(f"Import issues found ({len(import_issues)}):")
        for issue in import_issues:
            print(f"   - {issue}")
        total_issues += len(import_issues)
    else:
        print_status("No import issues found")
    
    # Validate package.json
    print_info("Validating frontend configuration...")
    is_valid, error = validate_package_json()
    if not is_valid:
        print_error(f"package.json validation failed: {error}")
        total_issues += 1
    else:
        print_status("Frontend package.json is valid")
    
    # Validate Docker configuration
    print_info("Checking Docker configuration...")
    if Path("docker-compose.yml").exists():
        print_status("Docker Compose configuration found")
        
        # Check if init.sql exists (referenced in docker-compose.yml)
        if Path("init.sql").exists():
            print_status("Database initialization script found")
        else:
            print_warning("init.sql not found (referenced in docker-compose.yml)")
    else:
        print_error("docker-compose.yml not found")
        total_issues += 1
    
    # Summary
    print("\n" + "=" * 60)
    if total_issues == 0:
        print_status("🎉 Project validation passed! No issues found.")
        print_info("The project appears to be properly configured and ready to run.")
    else:
        print_warning(f"⚠️  Project validation completed with {total_issues} issue(s).")
        print_info("Please review and fix the issues listed above.")
    
    return total_issues == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)