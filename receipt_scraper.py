"""
Receipt discovery and extraction from Costco orders page
"""

import json
import re
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urljoin

from browser_manager import BrowserManager
from config import Config
from receipt_models import Receipt, ReceiptBatch


class ReceiptScraper:
    """Scrapes receipt data from Costco orders page"""
    
    def __init__(self, browser_manager: BrowserManager, config: Config):
        self.browser = browser_manager
        self.config = config
        self.receipt_batch = ReceiptBatch()
    
    def discover_all_receipts(self) -> ReceiptBatch:
        """Discover all receipts across different time ranges"""
        print("🔍 Starting receipt discovery...")
        
        # Time ranges to check (Costco typically shows these options)
        time_ranges = [
            "Last 3 Months",
            "Last 6 Months", 
            "Last 12 Months",
            "2024",
            "2023",
            "2022"
        ]
        
        for time_range in time_ranges:
            print(f"📅 Checking receipts for: {time_range}")
            
            try:
                # Select time range
                if self._select_time_range(time_range):
                    # Scrape receipts from all pages in this time range
                    range_receipts = self._scrape_time_range()
                    print(f"✅ Found {len(range_receipts)} receipts in {time_range}")
                    
                    # Add to batch (with duplicate detection)
                    for receipt in range_receipts:
                        is_duplicate = self._is_duplicate_receipt(receipt)
                        self.receipt_batch.add_receipt(receipt, is_duplicate)
                
                else:
                    print(f"⚠️  Could not select time range: {time_range}")
                
                # Human-like delay between time ranges
                self.browser.human_delay(2, 5)
                
            except Exception as e:
                print(f"❌ Error processing {time_range}: {e}")
                self.receipt_batch.add_failed()
        
        print(f"🎉 Receipt discovery completed!")
        print(f"📊 Summary: {json.dumps(self.receipt_batch.summary(), indent=2)}")
        
        return self.receipt_batch
    
    def _select_time_range(self, time_range: str) -> bool:
        """Select a specific time range filter"""
        try:
            # Look for time range dropdown
            dropdown_selectors = [
                'select[aria-label*="time" i]',
                'select[aria-label*="range" i]',
                'select[aria-label*="period" i]',
                'select[name*="time" i]',
                'select[name*="period" i]',
                '.time-range-select',
                '.date-range-select'
            ]
            
            dropdown = None
            for selector in dropdown_selectors:
                try:
                    if self.browser.page.locator(selector).is_visible():
                        dropdown = selector
                        break
                except:
                    continue
            
            if not dropdown:
                print("❌ Could not find time range dropdown")
                return False
            
            # Click dropdown to open options
            self.browser.human_click(dropdown)
            self.browser.human_delay(0.5, 1.5)
            
            # Look for the specific time range option
            option_selectors = [
                f'option:has-text("{time_range}")',
                f'option[value*="{time_range.lower()}" i]',
                f'li:has-text("{time_range}")',
                f'[role="option"]:has-text("{time_range}")'
            ]
            
            for selector in option_selectors:
                try:
                    if self.browser.page.locator(selector).is_visible():
                        self.browser.human_click(selector)
                        self.browser.human_delay(1, 3)
                        print(f"✅ Selected time range: {time_range}")
                        return True
                except:
                    continue
            
            # Fallback: try selecting by index based on common patterns
            if "3 month" in time_range.lower():
                index = 1
            elif "6 month" in time_range.lower():
                index = 2
            elif "12 month" in time_range.lower():
                index = 3
            elif "2024" in time_range:
                index = 4
            elif "2023" in time_range:
                index = 5
            else:
                index = None
            
            if index:
                try:
                    self.browser.page.locator(f'{dropdown} option').nth(index).click()
                    self.browser.human_delay(1, 3)
                    print(f"✅ Selected time range by index: {time_range}")
                    return True
                except:
                    pass
            
            print(f"❌ Could not select time range: {time_range}")
            return False
            
        except Exception as e:
            print(f"❌ Error selecting time range {time_range}: {e}")
            return False
    
    def _scrape_time_range(self) -> List[Receipt]:
        """Scrape all receipts from current time range (across multiple pages)"""
        receipts = []
        page_number = 1
        
        while True:
            print(f"📄 Scraping page {page_number}...")
            
            # Wait for receipts to load
            self._wait_for_receipts_to_load()
            
            # Scrape current page
            page_receipts = self._scrape_current_page()
            
            if not page_receipts:
                print(f"🔚 No more receipts found on page {page_number}")
                break
            
            receipts.extend(page_receipts)
            print(f"✅ Found {len(page_receipts)} receipts on page {page_number}")
            
            # Try to go to next page
            if not self._go_to_next_page():
                print("🔚 No more pages available")
                break
            
            page_number += 1
            self.browser.human_delay(2, 4)
        
        return receipts
    
    def _wait_for_receipts_to_load(self, timeout: int = 15) -> bool:
        """Wait for receipts to appear on page"""
        try:
            # Wait for any receipt-like elements
            receipt_selectors = [
                '.receipt',
                '.transaction',
                '.order-item',
                '.purchase-item',
                '[data-testid*="receipt"]',
                '[data-testid*="order"]',
                '.order-row',
                '.transaction-row'
            ]
            
            for selector in receipt_selectors:
                try:
                    self.browser.page.wait_for_selector(selector, timeout=timeout * 1000)
                    print(f"✅ Receipts loaded (found: {selector})")
                    return True
                except:
                    continue
            
            print("⚠️  No receipt elements found, proceeding anyway")
            return False
            
        except Exception as e:
            print(f"⚠️  Error waiting for receipts: {e}")
            return False
    
    def _scrape_current_page(self) -> List[Receipt]:
        """Scrape receipts from current page"""
        receipts = []
        
        try:
            # Use JavaScript to extract receipt data
            receipt_data = self.browser.page.evaluate("""
                () => {
                    const receipts = [];
                    
                    // Look for various receipt container patterns
                    const containers = [
                        ...document.querySelectorAll('.receipt'),
                        ...document.querySelectorAll('.transaction'),
                        ...document.querySelectorAll('.order-item'),
                        ...document.querySelectorAll('.purchase-item'),
                        ...document.querySelectorAll('[data-testid*="receipt"]'),
                        ...document.querySelectorAll('[data-testid*="order"]'),
                        ...document.querySelectorAll('.order-row'),
                        ...document.querySelectorAll('tr[data-*]'),
                        ...document.querySelectorAll('[class*="order"]'),
                        ...document.querySelectorAll('[class*="receipt"]')
                    ];
                    
                    // Remove duplicates
                    const uniqueContainers = [...new Set(containers)];
                    
                    uniqueContainers.forEach((container, index) => {
                        try {
                            const receiptData = {
                                index: index,
                                html: container.outerHTML.substring(0, 1000), // Limit size
                                text: container.innerText?.substring(0, 500) || '',
                                attributes: {}
                            };
                            
                            // Extract common attributes
                            ['data-id', 'data-receipt-id', 'data-order-id', 'data-transaction-id', 'id', 'class'].forEach(attr => {
                                const value = container.getAttribute(attr);
                                if (value) receiptData.attributes[attr] = value;
                            });
                            
                            // Look for date patterns
                            const dateElements = container.querySelectorAll('*');
                            for (let el of dateElements) {
                                const text = el.innerText || '';
                                if (text.match(/\\d{1,2}[\\/\\-]\\d{1,2}[\\/\\-]\\d{2,4}/)) {
                                    receiptData.dateText = text.trim();
                                    break;
                                }
                            }
                            
                            // Look for amount patterns
                            const amountElements = container.querySelectorAll('*');
                            for (let el of amountElements) {
                                const text = el.innerText || '';
                                if (text.match(/\\$\\d+\\.\\d{2}/)) {
                                    receiptData.amountText = text.trim();
                                    break;
                                }
                            }
                            
                            // Look for location patterns
                            const locationElements = container.querySelectorAll('*');
                            for (let el of locationElements) {
                                const text = el.innerText || '';
                                if (text.toLowerCase().includes('costco') || text.match(/store|location|warehouse/i)) {
                                    receiptData.locationText = text.trim();
                                    break;
                                }
                            }
                            
                            receipts.push(receiptData);
                        } catch (e) {
                            console.log('Error processing container:', e);
                        }
                    });
                    
                    return receipts;
                }
            """)
            
            print(f"🔍 Found {len(receipt_data)} potential receipt containers")
            
            # Process each receipt container
            for data in receipt_data:
                try:
                    receipt = self._parse_receipt_data(data)
                    if receipt:
                        receipts.append(receipt)
                except Exception as e:
                    print(f"⚠️  Error parsing receipt {data.get('index', '?')}: {e}")
            
        except Exception as e:
            print(f"❌ Error scraping current page: {e}")
        
        return receipts
    
    def _parse_receipt_data(self, data: Dict[str, Any]) -> Optional[Receipt]:
        """Parse receipt data from scraped HTML/text"""
        try:
            # Extract ID
            receipt_id = (
                data.get('attributes', {}).get('data-receipt-id') or
                data.get('attributes', {}).get('data-order-id') or
                data.get('attributes', {}).get('data-transaction-id') or
                data.get('attributes', {}).get('id') or
                f"receipt_{data.get('index', 0)}_{int(time.time())}"
            )
            
            # Extract and parse date
            date_text = data.get('dateText', '')
            receipt_date = self._parse_date(date_text, data.get('text', ''))
            
            if not receipt_date:
                print(f"⚠️  Could not parse date for receipt {receipt_id}")
                return None
            
            # Extract amount
            amount_text = data.get('amountText', '')
            total_amount = self._parse_amount(amount_text, data.get('text', ''))
            
            if total_amount <= 0:
                print(f"⚠️  Could not parse amount for receipt {receipt_id}")
                return None
            
            # Extract location
            location_text = data.get('locationText', '')
            location = self._parse_location(location_text, data.get('text', ''))
            
            if not location:
                location = "Unknown Location"
            
            # Create receipt
            receipt = Receipt(
                id=receipt_id,
                date=receipt_date,
                location=location,
                total_amount=total_amount,
                raw_data=data
            )
            
            return receipt
            
        except Exception as e:
            print(f"❌ Error parsing receipt data: {e}")
            return None
    
    def _parse_date(self, date_text: str, full_text: str) -> Optional[datetime]:
        """Parse date from text"""
        # Combine texts for better matching
        combined_text = f"{date_text} {full_text}"
        
        # Date patterns to try
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}-\d{1,2}-\d{4})',
            r'(\d{4}-\d{1,2}-\d{1,2})',
            r'(\d{1,2}/\d{1,2}/\d{2})',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            if matches:
                date_str = matches[0]
                
                # Try to parse with different formats
                formats = [
                    '%m/%d/%Y',
                    '%m-%d-%Y', 
                    '%Y-%m-%d',
                    '%m/%d/%y',
                    '%B %d, %Y',
                    '%b %d, %Y',
                    '%B %d %Y',
                    '%b %d %Y'
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except:
                        continue
        
        return None
    
    def _parse_amount(self, amount_text: str, full_text: str) -> float:
        """Parse amount from text"""
        # Combine texts for better matching
        combined_text = f"{amount_text} {full_text}"
        
        # Amount patterns
        amount_patterns = [
            r'\$(\d+\.\d{2})',
            r'\$(\d+,\d+\.\d{2})',
            r'\$(\d+)',
            r'(\d+\.\d{2})',
            r'Total[:\s]*\$?(\d+\.\d{2})',
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            if matches:
                amount_str = matches[0].replace(',', '')
                try:
                    return float(amount_str)
                except:
                    continue
        
        return 0.0
    
    def _parse_location(self, location_text: str, full_text: str) -> str:
        """Parse location from text"""
        # Combine texts
        combined_text = f"{location_text} {full_text}"
        
        # Look for location patterns
        location_patterns = [
            r'Costco\s+([^,\n]+)',
            r'Store[:\s]+([^,\n]+)',
            r'Location[:\s]+([^,\n]+)',
            r'Warehouse[:\s]+([^,\n]+)',
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        # Fallback: look for any text that might be a location
        words = combined_text.split()
        for i, word in enumerate(words):
            if word.lower() in ['costco', 'warehouse', 'store'] and i + 1 < len(words):
                return ' '.join(words[i+1:i+4])  # Take next few words
        
        return "Unknown Location"
    
    def _go_to_next_page(self) -> bool:
        """Navigate to next page of receipts"""
        try:
            # Look for next page button
            next_selectors = [
                'button[aria-label*="next" i]',
                'a[aria-label*="next" i]',
                '.pagination-next',
                '.next-page',
                'button:has-text("Next")',
                'a:has-text("Next")',
                '[aria-label="Next page"]'
            ]
            
            for selector in next_selectors:
                try:
                    element = self.browser.page.locator(selector)
                    if element.is_visible() and element.is_enabled():
                        self.browser.human_click(selector)
                        print("➡️  Navigated to next page")
                        return True
                except:
                    continue
            
            print("🔚 No next page button found")
            return False
            
        except Exception as e:
            print(f"❌ Error navigating to next page: {e}")
            return False
    
    def _is_duplicate_receipt(self, receipt: Receipt) -> bool:
        """Check if receipt is a duplicate"""
        for existing in self.receipt_batch.receipts:
            if (existing.date.date() == receipt.date.date() and
                existing.location == receipt.location and
                abs(existing.total_amount - receipt.total_amount) < 0.01):
                return True
        return False