#!/usr/bin/env python3
"""
Installation script for Costco Receipt Tracker
Sets up Python environment and installs playwright browsers
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def check_python_version():
    """Check if Python version is suitable"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor} detected")

def main():
    print("🚀 Setting up Costco Receipt Tracker")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Upgrade pip first (recommended for Windows)
    print("🔄 Upgrading pip...")
    run_command("python -m pip install --upgrade pip", "Upgrading pip")
    
    # Install Python packages
    result = run_command("pip install -r requirements.txt", "Installing Python dependencies")
    if not result:
        print("❌ Failed to install Python packages")
        print("💡 Try running manually: pip install -r requirements.txt")
        sys.exit(1)
    
    # Install playwright browsers
    result = run_command("playwright install chromium", "Installing Playwright Chromium browser")
    if not result:
        print("❌ Failed to install Playwright browsers")
        print("💡 Try running manually: playwright install chromium")
        sys.exit(1)
    
    # Create necessary directories
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("sessions", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    print("✅ Created necessary directories")
    
    # Copy environment file if it doesn't exist
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            # Use copy command for Windows compatibility
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ Created .env file from template")
            print("📝 Please edit .env file with your Costco credentials")
        else:
            print("⚠️  .env.example not found, you'll need to create .env manually")
    
    print("\n🎉 Installation completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your Costco username and password")
    print("2. Run: python test_setup.py (to verify setup)")
    print("3. Run: python main.py (to start scraping)")

if __name__ == "__main__":
    main()