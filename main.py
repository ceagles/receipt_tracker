#!/usr/bin/env python3
"""
Costco Receipt Tracker - Main Application
Advanced web scraping with anti-detection for receipt data extraction
"""

import sys
import os
from datetime import datetime
from pathlib import Path

from config import Config
from browser_manager import BrowserManager
from authenticator import CostcoAuthenticator
from receipt_scraper import ReceiptScraper
from database import ReceiptDatabase


def main():
    """Main application entry point"""
    print("🏪 Costco Receipt Tracker")
    print("=" * 50)
    
    try:
        # Load configuration
        print("⚙️  Loading configuration...")
        config = Config.from_env()
        config.validate()
        print(f"✅ Configuration loaded - Download path: {config.download_path}")
        
        # Initialize database
        print("💾 Initializing database...")
        db = ReceiptDatabase()
        stats = db.get_statistics()
        if stats.get('total_receipts', 0) > 0:
            print(f"📊 Found {stats['total_receipts']} existing receipts in database")
        
        # Start browser with anti-detection
        print("🌐 Starting browser...")
        with BrowserManager(config) as browser:
            print("✅ Browser started successfully")
            
            # Initialize authenticator and scraper
            authenticator = CostcoAuthenticator(browser, config)
            scraper = ReceiptScraper(browser, config)
            
            # Perform authentication
            print("🔐 Authenticating with Costco...")
            auth_result = authenticator.login(config.username, config.password)
            
            if not auth_result.success:
                if auth_result.requires_2fa:
                    print("❌ 2FA required - please handle manually")
                    print("💡 You may need to:")
                    print("   1. Complete 2FA authentication manually")
                    print("   2. Save the session for reuse")
                    return 1
                else:
                    print(f"❌ Authentication failed: {auth_result.message}")
                    return 1
            
            print("✅ Authentication successful!")
            
            # Navigate to orders page
            if not authenticator.navigate_to_orders():
                print("❌ Failed to navigate to orders page")
                return 1
            
            # Find warehouse tab
            if not authenticator.find_warehouse_tab():
                print("❌ Failed to find warehouse receipts tab")
                return 1
            
            print("📦 Ready to scrape receipts!")
            
            # Discover and scrape receipts
            print("🔍 Starting receipt discovery...")
            receipt_batch = scraper.discover_all_receipts()
            
            if not receipt_batch or len(receipt_batch) == 0:
                print("⚠️  No receipts found")
                return 0
            
            # Save to database
            print("💾 Saving receipts to database...")
            save_stats = db.save_batch(receipt_batch)
            
            # Generate final report
            generate_report(receipt_batch, save_stats, db)
            
        print("🎉 Receipt tracking completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def generate_report(batch, save_stats, db):
    """Generate and display final report"""
    print("\n" + "=" * 60)
    print("📊 FINAL REPORT")
    print("=" * 60)
    
    # Scraping statistics
    batch_summary = batch.summary()
    print(f"🔍 Scraping Results:")
    print(f"   • Total processed: {batch_summary['total_processed']}")
    print(f"   • Successfully scraped: {batch_summary['successful']}")
    print(f"   • Failed: {batch_summary['failed']}")
    print(f"   • Duplicates skipped: {batch_summary['duplicates']}")
    print(f"   • Total amount: ${batch_summary['total_amount']:.2f}")
    
    if batch_summary['date_range']['start']:
        print(f"   • Date range: {batch_summary['date_range']['start'][:10]} to {batch_summary['date_range']['end'][:10]}")
    
    # Database statistics
    print(f"\n💾 Database Results:")
    print(f"   • Saved to database: {save_stats['saved']}")
    print(f"   • Already existed: {save_stats['skipped']}")
    print(f"   • Save failures: {save_stats['failed']}")
    
    # Overall database stats
    db_stats = db.get_statistics()
    print(f"\n📈 Overall Database Statistics:")
    print(f"   • Total receipts: {db_stats.get('total_receipts', 0)}")
    print(f"   • Total amount: ${db_stats.get('total_amount', 0):.2f}")
    print(f"   • Average amount: ${db_stats.get('average_amount', 0):.2f}")
    
    # Top locations
    top_locations = db_stats.get('top_locations', [])
    if top_locations:
        print(f"\n🏪 Top Locations:")
        for loc in top_locations[:3]:
            print(f"   • {loc['location']}: {loc['count']} receipts (${loc['total']:.2f})")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    sys.exit(main())