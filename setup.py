#!/usr/bin/env python3
"""
Setup script for Telegram Finance Bot
Helps initialize the project and check dependencies
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*50)
    print(f" {text}")
    print("="*50)

def print_step(step_num, text):
    """Print formatted step"""
    print(f"\n[Step {step_num}] {text}")

def check_python_version():
    """Check if Python version is compatible"""
    print_step(1, "Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def create_directories():
    """Create necessary directories"""
    print_step(2, "Creating directories...")
    
    directories = [
        'bot',
        'services', 
        'utils',
        'data',
        'logs',
        'exports',
        'backups'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def install_dependencies():
    """Install Python dependencies"""
    print_step(3, "Installing dependencies...")
    
    try:
        # Check if pip is available
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, capture_output=True)
        
        # Install dependencies
        print("Installing packages from requirements.txt...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("Please install dependencies manually:")
        print("pip install -r requirements.txt")
        return False
    except FileNotFoundError:
        print("❌ pip not found. Please install pip first.")
        return False

def setup_environment_file():
    """Setup environment configuration"""
    print_step(4, "Setting up environment configuration...")
    
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your configuration:")
            print("   - TELEGRAM_BOT_TOKEN")
            print("   - GEMINI_API_KEY")
        else:
            # Create basic .env file
            with open('.env', 'w') as f:
                f.write("# Telegram Finance Bot Configuration\n")
                f.write("TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE\n")
                f.write("GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE\n")
                f.write("TIMEZONE=Asia/Jakarta\n")
                f.write("CURRENCY=IDR\n")
            print("✅ Created basic .env file")
    else:
        print("✅ .env file already exists")

def check_credentials():
    """Check for Google credentials"""
    print_step(5, "Checking Google credentials...")
    
    if not os.path.exists('credentials.json'):
        print("⚠️  credentials.json not found")
        print("Please download OAuth 2.0 credentials from Google Cloud Console:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Enable Google Sheets API")
        print("3. Create OAuth 2.0 credentials")
        print("4. Download and rename to 'credentials.json'")
    else:
        print("✅ credentials.json found")

def create_categories_file():
    """Create default categories file if not exists"""
    print_step(6, "Setting up categories...")
    
    if not os.path.exists('data/categories.json'):
        print("⚠️  data/categories.json not found")
        print("Please ensure the categories.json file is in the data/ directory")
    else:
        print("✅ Categories file found")

def validate_setup():
    """Validate the setup"""
    print_step(7, "Validating setup...")
    
    required_files = [
        'main.py',
        'config.py', 
        'requirements.txt',
        '.env',
        'bot/__init__.py',
        'services/__init__.py',
        'utils/__init__.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ All required files are present")
    return True

def print_next_steps():
    """Print next steps for user"""
    print_header("NEXT STEPS")
    
    steps = [
        "1. Edit .env file with your bot token and API keys",
        "2. Download credentials.json from Google Cloud Console",
        "3. Run 'python main.py' to start the bot",
        "4. Test the bot by sending /start in Telegram"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    print("\n📚 Documentation:")
    print("   - README.md for detailed setup instructions")
    print("   - Check bot/handlers.py for available commands")
    
    print("\n🆘 Need help?")
    print("   - Check the troubleshooting section in README.md")
    print("   - Ensure all API keys are correctly configured")

def run_tests():
    """Run basic tests to verify setup"""
    print_step(8, "Running basic tests...")
    
    try:
        # Test imports
        print("Testing imports...")
        
        import telegram
        print("✅ python-telegram-bot imported successfully")
        
        import google.auth
        print("✅ google-auth imported successfully")
        
        import google.generativeai
        print("✅ google-generativeai imported successfully")
        
        # Test config loading
        try:
            from config import Config
            print("✅ Configuration loaded successfully")
        except Exception as e:
            print(f"⚠️  Configuration warning: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please check if all dependencies are installed correctly")
        return False

def main():
    """Main setup function"""
    print_header("TELEGRAM FINANCE BOT SETUP")
    print("This script will help you set up the Telegram Finance Bot")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("⚠️  Continuing with manual dependency installation...")
    
    # Setup environment
    setup_environment_file()
    
    # Check credentials
    check_credentials()
    
    # Setup categories
    create_categories_file()
    
    # Validate setup
    if not validate_setup():
        print("❌ Setup validation failed")
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        print("⚠️  Some tests failed, but setup may still work")
    
    # Print next steps
    print_next_steps()
    
    print_header("SETUP COMPLETE")
    print("✅ Setup completed successfully!")
    print("You can now run 'python main.py' to start the bot")

if __name__ == "__main__":
    main()