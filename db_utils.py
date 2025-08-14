#!/usr/bin/env python3
"""
Database utilities for receipt management
"""

import sys
import argparse
from datetime import datetime, timedelta
from database import ReceiptDatabase


def list_receipts(db, limit=10):
    """List recent receipts"""
    receipts = db.get_all_receipts(limit=limit)
    
    if not receipts:
        print("No receipts found in database")
        return
    
    print(f"📋 Last {len(receipts)} receipts:")
    print("-" * 80)
    
    for receipt in receipts:
        print(f"{receipt.date.strftime('%Y-%m-%d %H:%M')} | "
              f"{receipt.location:20} | "
              f"${receipt.total_amount:8.2f} | "
              f"{receipt.id}")


def show_statistics(db):
    """Show database statistics"""
    stats = db.get_statistics()
    
    print("📊 Database Statistics")
    print("=" * 50)
    print(f"Total receipts: {stats.get('total_receipts', 0)}")
    print(f"Total amount: ${stats.get('total_amount', 0):.2f}")
    print(f"Average amount: ${stats.get('average_amount', 0):.2f}")
    print(f"Amount range: ${stats.get('min_amount', 0):.2f} - ${stats.get('max_amount', 0):.2f}")
    
    date_range = stats.get('date_range', {})
    if date_range.get('earliest'):
        print(f"Date range: {date_range['earliest'][:10]} to {date_range['latest'][:10]}")
    
    print(f"\n🏪 Top Locations:")
    for loc in stats.get('top_locations', []):
        print(f"  {loc['location']:25} {loc['count']:3} receipts  ${loc['total']:8.2f}")


def search_receipts(db, location=None, days=None, min_amount=None, max_amount=None):
    """Search receipts with filters"""
    date_from = None
    if days:
        date_from = datetime.now() - timedelta(days=days)
    
    receipts = db.search_receipts(
        location=location,
        date_from=date_from,
        min_amount=min_amount,
        max_amount=max_amount
    )
    
    if not receipts:
        print("No receipts found matching criteria")
        return
    
    print(f"🔍 Found {len(receipts)} matching receipts:")
    print("-" * 80)
    
    total = 0
    for receipt in receipts:
        print(f"{receipt.date.strftime('%Y-%m-%d %H:%M')} | "
              f"{receipt.location:20} | "
              f"${receipt.total_amount:8.2f} | "
              f"{receipt.id}")
        total += receipt.total_amount
    
    print("-" * 80)
    print(f"Total: ${total:.2f}")


def delete_receipt(db, receipt_id):
    """Delete a specific receipt"""
    if db.delete_receipt(receipt_id):
        print(f"✅ Deleted receipt: {receipt_id}")
    else:
        print(f"❌ Receipt not found: {receipt_id}")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Receipt database utilities")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List recent receipts')
    list_parser.add_argument('--limit', type=int, default=10, help='Number of receipts to show')
    
    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search receipts')
    search_parser.add_argument('--location', help='Filter by location')
    search_parser.add_argument('--days', type=int, help='Last N days')
    search_parser.add_argument('--min-amount', type=float, help='Minimum amount')
    search_parser.add_argument('--max-amount', type=float, help='Maximum amount')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a receipt')
    delete_parser.add_argument('receipt_id', help='Receipt ID to delete')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize database
    db = ReceiptDatabase()
    
    try:
        if args.command == 'list':
            list_receipts(db, args.limit)
        elif args.command == 'stats':
            show_statistics(db)
        elif args.command == 'search':
            search_receipts(db, args.location, args.days, args.min_amount, args.max_amount)
        elif args.command == 'delete':
            delete_receipt(db, args.receipt_id)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())