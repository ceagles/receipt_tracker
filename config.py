"""
Configuration management for Costco Receipt Tracker
"""

import os
import random
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    """Application configuration"""
    username: str
    password: str
    download_path: str
    headless: bool
    max_retries: int
    delay_min: int
    delay_max: int
    proxy_url: Optional[str] = None
    session_path: str = "./sessions"
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create config from environment variables"""
        return cls(
            username=os.getenv('COSTCO_USERNAME', ''),
            password=os.getenv('COSTCO_PASSWORD', ''),
            download_path=os.getenv('DOWNLOAD_PATH', './downloads'),
            headless=os.getenv('HEADLESS', 'false').lower() == 'true',
            max_retries=int(os.getenv('MAX_RETRIES', '3')),
            delay_min=int(os.getenv('DELAY_MIN', '2')),
            delay_max=int(os.getenv('DELAY_MAX', '8')),
            proxy_url=os.getenv('PROXY_URL'),
            session_path=os.getenv('SESSION_PATH', './sessions')
        )
    
    def validate(self) -> None:
        """Validate configuration"""
        if not self.username:
            raise ValueError("COSTCO_USERNAME environment variable is required")
        if not self.password:
            raise ValueError("COSTCO_PASSWORD environment variable is required")
        
        # Create directories if they don't exist
        os.makedirs(self.download_path, exist_ok=True)
        os.makedirs(self.session_path, exist_ok=True)
    
    def random_delay(self) -> float:
        """Get random delay between min and max"""
        return random.uniform(self.delay_min, self.delay_max)

# Browser configuration for realistic behavior
BROWSER_CONFIG = {
    'user_agents': [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ],
    'viewports': [
        {'width': 1920, 'height': 1080},
        {'width': 1366, 'height': 768},
        {'width': 1440, 'height': 900},
        {'width': 1536, 'height': 864},
    ],
    'languages': ['en-US', 'en'],
    'timezones': ['America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles'],
}