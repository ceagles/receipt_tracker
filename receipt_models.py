"""
Data models for receipt information
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import re


@dataclass
class Receipt:
    """Individual receipt data"""
    id: str
    date: datetime
    location: str
    total_amount: float
    currency: str = "USD"
    receipt_number: Optional[str] = None
    member_number: Optional[str] = None
    items: List[Dict[str, Any]] = field(default_factory=list)
    tax_amount: Optional[float] = None
    subtotal_amount: Optional[float] = None
    pdf_path: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and clean data after initialization"""
        # Clean location name
        if self.location:
            self.location = self._clean_location(self.location)
        
        # Ensure amount is properly formatted
        if isinstance(self.total_amount, str):
            self.total_amount = self._parse_amount(self.total_amount)
    
    def _clean_location(self, location: str) -> str:
        """Clean and standardize location name"""
        # Remove extra whitespace
        location = ' '.join(location.split())
        
        # Remove common prefixes/suffixes
        location = re.sub(r'^(Costco\s*Wholesale\s*|Costco\s*)', '', location, flags=re.IGNORECASE)
        location = re.sub(r'\s*(Warehouse|Store)\s*$', '', location, flags=re.IGNORECASE)
        
        return location.strip()
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        # Remove currency symbols and whitespace
        amount_str = re.sub(r'[$,\s]', '', str(amount_str))
        
        try:
            return float(amount_str)
        except ValueError:
            return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'location': self.location,
            'total_amount': self.total_amount,
            'currency': self.currency,
            'receipt_number': self.receipt_number,
            'member_number': self.member_number,
            'items': self.items,
            'tax_amount': self.tax_amount,
            'subtotal_amount': self.subtotal_amount,
            'pdf_path': self.pdf_path,
            'raw_data': self.raw_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Receipt':
        """Create Receipt from dictionary"""
        data = data.copy()
        if 'date' in data and isinstance(data['date'], str):
            data['date'] = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
        
        return cls(**data)
    
    def filename(self) -> str:
        """Generate standardized filename for PDF"""
        date_str = self.date.strftime("%Y-%m-%d_%H-%M-%S")
        location_clean = re.sub(r'[^\w\s-]', '', self.location).strip().replace(' ', '_')
        amount_str = f"${self.total_amount:.2f}".replace('.', '-')
        
        return f"Costco_{date_str}_{location_clean}_{amount_str}.pdf"
    
    def __str__(self) -> str:
        return f"Receipt({self.date.strftime('%Y-%m-%d')}, {self.location}, ${self.total_amount:.2f})"


@dataclass
class ReceiptBatch:
    """Collection of receipts with metadata"""
    receipts: List[Receipt] = field(default_factory=list)
    total_count: int = 0
    scraped_count: int = 0
    failed_count: int = 0
    duplicate_count: int = 0
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    
    def add_receipt(self, receipt: Receipt, is_duplicate: bool = False) -> None:
        """Add a receipt to the batch"""
        if not is_duplicate:
            self.receipts.append(receipt)
            self.scraped_count += 1
        else:
            self.duplicate_count += 1
        
        self.total_count += 1
        
        # Update date range
        if not self.date_range_start or receipt.date < self.date_range_start:
            self.date_range_start = receipt.date
        if not self.date_range_end or receipt.date > self.date_range_end:
            self.date_range_end = receipt.date
    
    def add_failed(self) -> None:
        """Record a failed scraping attempt"""
        self.failed_count += 1
        self.total_count += 1
    
    def summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            'total_receipts': len(self.receipts),
            'total_processed': self.total_count,
            'successful': self.scraped_count,
            'failed': self.failed_count,
            'duplicates': self.duplicate_count,
            'date_range': {
                'start': self.date_range_start.isoformat() if self.date_range_start else None,
                'end': self.date_range_end.isoformat() if self.date_range_end else None
            },
            'total_amount': sum(r.total_amount for r in self.receipts),
            'locations': list(set(r.location for r in self.receipts))
        }
    
    def __len__(self) -> int:
        return len(self.receipts)
    
    def __iter__(self):
        return iter(self.receipts)