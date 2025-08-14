"""
SQLite database management for receipt data
Compatible with the Go Receipt struct: Date, Location, Total, ID
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from receipt_models import Receipt, ReceiptBatch


class ReceiptDatabase:
    """SQLite database for storing receipt data"""
    
    def __init__(self, db_path: str = "receipts.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Main receipts table - compatible with Go struct
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS receipts (
                    id TEXT PRIMARY KEY,
                    date DATETIME NOT NULL,
                    location TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    receipt_number TEXT,
                    member_number TEXT,
                    tax_amount REAL,
                    subtotal_amount REAL,
                    pdf_path TEXT,
                    raw_data TEXT,  -- JSON string
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Receipt items table for detailed item information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS receipt_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id TEXT NOT NULL,
                    item_name TEXT,
                    item_price REAL,
                    quantity INTEGER,
                    item_number TEXT,
                    department TEXT,
                    FOREIGN KEY (receipt_id) REFERENCES receipts (id)
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_receipts_date ON receipts (date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_receipts_location ON receipts (location)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_receipts_amount ON receipts (total_amount)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_receipt_items_receipt_id ON receipt_items (receipt_id)")
            
            conn.commit()
            print("✅ Database initialized successfully")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def save_receipt(self, receipt: Receipt) -> bool:
        """Save a single receipt to database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if receipt already exists
                cursor.execute("SELECT id FROM receipts WHERE id = ?", (receipt.id,))
                if cursor.fetchone():
                    print(f"⚠️  Receipt {receipt.id} already exists, skipping")
                    return False
                
                # Insert receipt
                cursor.execute("""
                    INSERT INTO receipts (
                        id, date, location, total_amount, currency,
                        receipt_number, member_number, tax_amount, 
                        subtotal_amount, pdf_path, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    receipt.id,
                    receipt.date.isoformat(),
                    receipt.location,
                    receipt.total_amount,
                    receipt.currency,
                    receipt.receipt_number,
                    receipt.member_number,
                    receipt.tax_amount,
                    receipt.subtotal_amount,
                    receipt.pdf_path,
                    json.dumps(receipt.raw_data) if receipt.raw_data else None
                ))
                
                # Insert receipt items if available
                for item in receipt.items:
                    cursor.execute("""
                        INSERT INTO receipt_items (
                            receipt_id, item_name, item_price, quantity, 
                            item_number, department
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        receipt.id,
                        item.get('name'),
                        item.get('price'),
                        item.get('quantity'),
                        item.get('item_number'),
                        item.get('department')
                    ))
                
                conn.commit()
                print(f"✅ Saved receipt: {receipt}")
                return True
                
        except Exception as e:
            print(f"❌ Error saving receipt {receipt.id}: {e}")
            return False
    
    def save_batch(self, batch: ReceiptBatch) -> Dict[str, int]:
        """Save a batch of receipts"""
        stats = {'saved': 0, 'skipped': 0, 'failed': 0}
        
        print(f"💾 Saving {len(batch)} receipts to database...")
        
        for receipt in batch:
            try:
                if self.save_receipt(receipt):
                    stats['saved'] += 1
                else:
                    stats['skipped'] += 1
            except Exception as e:
                print(f"❌ Failed to save receipt {receipt.id}: {e}")
                stats['failed'] += 1
        
        print(f"📊 Batch save completed: {stats}")
        return stats
    
    def get_receipt(self, receipt_id: str) -> Optional[Receipt]:
        """Get a specific receipt by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get receipt data
                cursor.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                # Get receipt items
                cursor.execute("SELECT * FROM receipt_items WHERE receipt_id = ?", (receipt_id,))
                items = []
                for item_row in cursor.fetchall():
                    items.append({
                        'name': item_row['item_name'],
                        'price': item_row['item_price'],
                        'quantity': item_row['quantity'],
                        'item_number': item_row['item_number'],
                        'department': item_row['department']
                    })
                
                # Create Receipt object
                receipt = Receipt(
                    id=row['id'],
                    date=datetime.fromisoformat(row['date']),
                    location=row['location'],
                    total_amount=row['total_amount'],
                    currency=row['currency'],
                    receipt_number=row['receipt_number'],
                    member_number=row['member_number'],
                    items=items,
                    tax_amount=row['tax_amount'],
                    subtotal_amount=row['subtotal_amount'],
                    pdf_path=row['pdf_path'],
                    raw_data=json.loads(row['raw_data']) if row['raw_data'] else {}
                )
                
                return receipt
                
        except Exception as e:
            print(f"❌ Error getting receipt {receipt_id}: {e}")
            return None
    
    def get_all_receipts(self, limit: Optional[int] = None, offset: int = 0) -> List[Receipt]:
        """Get all receipts with optional pagination"""
        receipts = []
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM receipts ORDER BY date DESC"
                params = []
                
                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                
                cursor.execute(query, params)
                
                for row in cursor.fetchall():
                    receipt = Receipt(
                        id=row['id'],
                        date=datetime.fromisoformat(row['date']),
                        location=row['location'],
                        total_amount=row['total_amount'],
                        currency=row['currency'],
                        receipt_number=row['receipt_number'],
                        member_number=row['member_number'],
                        tax_amount=row['tax_amount'],
                        subtotal_amount=row['subtotal_amount'],
                        pdf_path=row['pdf_path'],
                        raw_data=json.loads(row['raw_data']) if row['raw_data'] else {}
                    )
                    receipts.append(receipt)
                    
        except Exception as e:
            print(f"❌ Error getting receipts: {e}")
        
        return receipts
    
    def search_receipts(self, 
                       location: Optional[str] = None,
                       date_from: Optional[datetime] = None,
                       date_to: Optional[datetime] = None,
                       min_amount: Optional[float] = None,
                       max_amount: Optional[float] = None) -> List[Receipt]:
        """Search receipts with filters"""
        receipts = []
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM receipts WHERE 1=1"
                params = []
                
                if location:
                    query += " AND location LIKE ?"
                    params.append(f"%{location}%")
                
                if date_from:
                    query += " AND date >= ?"
                    params.append(date_from.isoformat())
                
                if date_to:
                    query += " AND date <= ?"
                    params.append(date_to.isoformat())
                
                if min_amount:
                    query += " AND total_amount >= ?"
                    params.append(min_amount)
                
                if max_amount:
                    query += " AND total_amount <= ?"
                    params.append(max_amount)
                
                query += " ORDER BY date DESC"
                
                cursor.execute(query, params)
                
                for row in cursor.fetchall():
                    receipt = Receipt(
                        id=row['id'],
                        date=datetime.fromisoformat(row['date']),
                        location=row['location'],
                        total_amount=row['total_amount'],
                        currency=row['currency'],
                        receipt_number=row['receipt_number'],
                        member_number=row['member_number'],
                        tax_amount=row['tax_amount'],
                        subtotal_amount=row['subtotal_amount'],
                        pdf_path=row['pdf_path'],
                        raw_data=json.loads(row['raw_data']) if row['raw_data'] else {}
                    )
                    receipts.append(receipt)
                    
        except Exception as e:
            print(f"❌ Error searching receipts: {e}")
        
        return receipts
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Basic counts
                cursor.execute("SELECT COUNT(*) FROM receipts")
                total_receipts = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM receipt_items")
                total_items = cursor.fetchone()[0]
                
                # Amount statistics
                cursor.execute("SELECT SUM(total_amount), AVG(total_amount), MIN(total_amount), MAX(total_amount) FROM receipts")
                amount_stats = cursor.fetchone()
                
                # Date range
                cursor.execute("SELECT MIN(date), MAX(date) FROM receipts")
                date_range = cursor.fetchone()
                
                # Top locations
                cursor.execute("""
                    SELECT location, COUNT(*) as count, SUM(total_amount) as total 
                    FROM receipts 
                    GROUP BY location 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                top_locations = cursor.fetchall()
                
                return {
                    'total_receipts': total_receipts,
                    'total_items': total_items,
                    'total_amount': amount_stats[0] or 0,
                    'average_amount': amount_stats[1] or 0,
                    'min_amount': amount_stats[2] or 0,
                    'max_amount': amount_stats[3] or 0,
                    'date_range': {
                        'earliest': date_range[0],
                        'latest': date_range[1]
                    },
                    'top_locations': [
                        {'location': row[0], 'count': row[1], 'total': row[2]}
                        for row in top_locations
                    ]
                }
                
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return {}
    
    def receipt_exists(self, receipt_id: str) -> bool:
        """Check if receipt exists in database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM receipts WHERE id = ? LIMIT 1", (receipt_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"❌ Error checking receipt existence: {e}")
            return False
    
    def delete_receipt(self, receipt_id: str) -> bool:
        """Delete a receipt and its items"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete items first (foreign key constraint)
                cursor.execute("DELETE FROM receipt_items WHERE receipt_id = ?", (receipt_id,))
                
                # Delete receipt
                cursor.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    print(f"✅ Deleted receipt: {receipt_id}")
                    return True
                else:
                    print(f"⚠️  Receipt not found: {receipt_id}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error deleting receipt {receipt_id}: {e}")
            return False