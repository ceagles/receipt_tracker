#!/usr/bin/env python3
"""
Test script to verify the setup is working correctly
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import playwright
        print("✅ Playwright available")
    except ImportError as e:
        print(f"❌ Playwright not available: {e}")
        return False
    
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright sync API available")
    except ImportError as e:
        print(f"❌ Playwright sync API not available: {e}")
        return False
    
    try:
        import sqlite3
        print("✅ SQLite3 available")
    except ImportError as e:
        print(f"❌ SQLite3 not available: {e}")
        return False
    
    # Test our modules
    modules_to_test = [
        'config',
        'browser_manager', 
        'authenticator',
        'receipt_scraper',
        'receipt_models',
        'database',
        'error_handler'
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module} module available")
        except ImportError as e:
            print(f"❌ {module} module not available: {e}")
            return False
    
    return True

def test_browser():
    """Test browser functionality"""
    print("\n🌐 Testing browser...")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Test if chromium is available
            browser = p.chromium.launch(headless=True)
            print("✅ Chromium browser available")
            
            page = browser.new_page()
            page.goto("https://httpbin.org/get")
            
            if "httpbin" in page.title().lower():
                print("✅ Basic navigation working")
            else:
                print("⚠️  Navigation may have issues")
            
            browser.close()
            return True
            
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\n💾 Testing database...")
    
    try:
        from database import ReceiptDatabase
        from receipt_models import Receipt
        from datetime import datetime
        
        # Create test database
        test_db = ReceiptDatabase("test_receipts.db")
        print("✅ Database creation successful")
        
        # Test adding a receipt
        test_receipt = Receipt(
            id="test_receipt_001",
            date=datetime.now(),
            location="Test Costco",
            total_amount=123.45
        )
        
        success = test_db.save_receipt(test_receipt)
        if success:
            print("✅ Receipt save successful")
        
        # Test retrieval
        retrieved = test_db.get_receipt("test_receipt_001")
        if retrieved and retrieved.id == "test_receipt_001":
            print("✅ Receipt retrieval successful")
        
        # Test statistics
        stats = test_db.get_statistics()
        if stats.get('total_receipts', 0) >= 1:
            print("✅ Statistics generation successful")
        
        # Cleanup
        os.remove("test_receipts.db")
        print("✅ Test cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n⚙️  Testing configuration...")
    
    try:
        from config import Config
        
        # Test without environment variables
        config = Config.from_env()
        print("✅ Configuration object creation successful")
        
        # Check that it has expected attributes
        required_attrs = ['username', 'password', 'download_path', 'headless', 'max_retries']
        for attr in required_attrs:
            if hasattr(config, attr):
                print(f"✅ Configuration has {attr}")
            else:
                print(f"❌ Configuration missing {attr}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_environment():
    """Test environment setup"""
    print("\n🌍 Testing environment...")
    
    # Check Python version
    if sys.version_info >= (3, 8):
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    else:
        print(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} is too old (need 3.8+)")
        return False
    
    # Check required directories
    required_dirs = ['downloads', 'sessions', 'logs']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ {dir_name} directory exists")
        else:
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"✅ Created {dir_name} directory")
            except Exception as e:
                print(f"❌ Could not create {dir_name} directory: {e}")
                return False
    
    # Check .env file
    if Path('.env').exists():
        print("✅ .env file exists")
    else:
        print("⚠️  .env file not found - you'll need to create it with your credentials")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Costco Receipt Tracker - Setup Test")
    print("=" * 50)
    
    tests = [
        ("Environment", test_environment),
        ("Imports", test_imports),
        ("Configuration", test_configuration), 
        ("Database", test_database),
        ("Browser", test_browser)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Create .env file with your Costco credentials")
        print("2. Run: python main.py")
        return 0
    else:
        print(f"\n⚠️  {len(tests) - passed} tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())