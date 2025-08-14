# Costco Receipt Tracker

Advanced Python-based tool for automatically scraping and storing Costco warehouse receipt data with sophisticated anti-detection measures.

## Features

- 🔐 **Advanced Authentication**: Bypasses bot detection with human-like behavior
- 🧠 **Anti-Detection**: Realistic browser fingerprinting and session management
- 📄 **Receipt Discovery**: Automatically finds and extracts receipt data across multiple time ranges
- 💾 **SQLite Storage**: Stores receipt data in a local database for easy querying
- 🔄 **Session Persistence**: Reuses authenticated sessions to minimize login frequency
- ⚡ **Rate Limiting**: Prevents overwhelming Costco's servers
- 📊 **Reporting**: Comprehensive statistics and search capabilities

## Quick Start

### 1. Installation

```bash
# Install dependencies
python install.py

# Or manually:
pip install -r requirements.txt
playwright install chromium
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

Set your Costco credentials:
```
COSTCO_USERNAME=your_email@example.com
COSTCO_PASSWORD=your_password
```

### 3. Run the Scraper

```bash
python main.py
```

## Usage

### Main Application
```bash
python main.py  # Start receipt scraping
```

### Database Utilities
```bash
# View recent receipts
python db_utils.py list --limit 20

# Show statistics
python db_utils.py stats

# Search receipts
python db_utils.py search --location "Seattle" --days 30
python db_utils.py search --min-amount 50 --max-amount 200

# Delete a receipt
python db_utils.py delete receipt_id_here
```

## Configuration Options

Edit `.env` file:

```bash
# Required
COSTCO_USERNAME=your_email@example.com
COSTCO_PASSWORD=your_password

# Optional
DOWNLOAD_PATH=./downloads          # Where to save PDFs
HEADLESS=false                     # Run browser in headless mode
MAX_RETRIES=3                      # Login retry attempts
DELAY_MIN=2                        # Minimum delay between actions (seconds)
DELAY_MAX=8                        # Maximum delay between actions (seconds)
```

## Database Schema

The tool creates a SQLite database with two main tables:

### receipts
- `id` - Unique receipt identifier
- `date` - Receipt date and time
- `location` - Store location
- `total_amount` - Total amount spent
- `currency` - Currency (default: USD)
- `receipt_number` - Costco receipt number
- `member_number` - Member number
- `tax_amount` - Tax amount
- `subtotal_amount` - Subtotal before tax
- `pdf_path` - Path to downloaded PDF
- `raw_data` - Original scraped data (JSON)

### receipt_items
- `receipt_id` - Links to receipts table
- `item_name` - Product name
- `item_price` - Individual item price
- `quantity` - Quantity purchased
- `item_number` - Costco item number
- `department` - Product department

## Anti-Detection Features

1. **Realistic Browser Configuration**
   - Random user agents and viewports
   - Proper browser headers and fingerprinting
   - JavaScript execution environment spoofing

2. **Human-like Behavior**
   - Random delays between actions
   - Mouse movement simulation
   - Realistic typing speeds with occasional "mistakes"

3. **Session Management**
   - Persistent cookies and authentication
   - Long-term session reuse
   - Proper session cleanup

4. **Rate Limiting**
   - Configurable request timing
   - Automatic backoff on errors
   - Memory and resource monitoring

## Troubleshooting

### Authentication Issues
```bash
# Check if 2FA is enabled on your account
# Consider disabling 2FA temporarily for automation

# If login fails repeatedly:
rm sessions/costco_session.pkl  # Clear saved session
```

### Bot Detection
```bash
# If you get blocked:
1. Wait 10-15 minutes before retrying
2. Clear browser sessions: rm sessions/*
3. Consider using a VPN
4. Try during off-peak hours (early morning)
```

### Browser Issues
```bash
# Reinstall browser
playwright install chromium --force

# Check browser availability
python -c "from playwright.sync_api import sync_playwright; print('Browser available')"
```

### Memory Issues
```bash
# Monitor memory usage
pip install psutil  # For memory monitoring

# Reduce batch size or add delays if memory usage is high
```

## File Structure

```
receipt_tracker/
├── main.py              # Main application
├── config.py            # Configuration management
├── browser_manager.py   # Browser control with anti-detection
├── authenticator.py     # Costco login handling
├── receipt_scraper.py   # Receipt discovery and extraction
├── receipt_models.py    # Data models
├── database.py          # SQLite database operations
├── error_handler.py     # Error handling and rate limiting
├── db_utils.py          # Database utilities CLI
├── install.py           # Installation script
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
└── README_python.md    # This file
```

## Security Notes

- **Credentials**: Store credentials in `.env` file (never commit to git)
- **Rate Limiting**: Built-in protections prevent overwhelming Costco's servers
- **Legal Compliance**: Only access your own account data
- **Session Security**: Sessions are stored locally and encrypted

## Limitations

- **2FA**: Manual intervention required for two-factor authentication
- **Rate Limits**: Respects Costco's server limits (may take time for large datasets)
- **Browser Dependency**: Requires Chromium browser
- **Network**: Stable internet connection required

## License

This tool is for personal use only. Respect Costco's Terms of Service and use responsibly.