"""
Browser management with anti-detection and session persistence
"""

import json
import os
import random
import pickle
from typing import Optional, Dict, Any
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
from playwright_stealth import stealth_sync

from config import Config, BROWSER_CONFIG


class BrowserManager:
    """Manages browser instances with anti-detection and session persistence"""
    
    def __init__(self, config: Config):
        self.config = config
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.session_file = os.path.join(config.session_path, "costco_session.pkl")
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def start(self) -> None:
        """Start browser with realistic configuration"""
        self.playwright = sync_playwright().start()
        
        # Configure browser launch options
        launch_options = {
            'headless': self.config.headless,
            'args': [
                '--no-first-run',
                '--no-service-autorun',
                '--password-store=basic',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-ipc-flooding-protection',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-background-timer-throttling',
                '--force-color-profile=srgb',
                '--disable-web-security',
                '--disable-features=TranslateUI',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        }
        
        # Add proxy if configured
        if self.config.proxy_url:
            proxy_parts = self.config.proxy_url.replace('http://', '').split('@')
            if len(proxy_parts) == 2:
                auth, server = proxy_parts
                username, password = auth.split(':')
                launch_options['proxy'] = {
                    'server': f"http://{server}",
                    'username': username,
                    'password': password
                }
            else:
                launch_options['proxy'] = {'server': self.config.proxy_url}
        
        # Launch browser
        self.browser = self.playwright.chromium.launch(**launch_options)
        
        # Create context with realistic settings
        context_options = self._get_context_options()
        self.context = self.browser.new_context(**context_options)
        
        # Load saved session if available
        self._load_session()
        
        # Create page
        self.page = self.context.new_page()
        
        # Apply stealth settings
        stealth_sync(self.page)
        
        # Add realistic behaviors
        self._setup_realistic_behaviors()
    
    def _get_context_options(self) -> Dict[str, Any]:
        """Get realistic context options"""
        viewport = random.choice(BROWSER_CONFIG['viewports'])
        user_agent = random.choice(BROWSER_CONFIG['user_agents'])
        
        return {
            'viewport': viewport,
            'user_agent': user_agent,
            'locale': 'en-US',
            'timezone_id': random.choice(BROWSER_CONFIG['timezones']),
            'permissions': ['geolocation'],
            'extra_http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
        }
    
    def _setup_realistic_behaviors(self) -> None:
        """Setup realistic browser behaviors"""
        # Override navigator.webdriver
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        # Override Chrome runtime
        self.page.add_init_script("""
            window.chrome = {
                runtime: {},
            };
        """)
        
        # Override permissions
        self.page.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            return window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        # Randomize canvas fingerprint
        self.page.add_init_script("""
            const getImageData = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(format) {
                if (format === 'image/png') {
                    const canvas = this;
                    const ctx = canvas.getContext('2d');
                    ctx.globalCompositeOperation = 'screen';
                    ctx.fillStyle = `rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.random()})`;
                    ctx.fillRect(0, 0, 1, 1);
                }
                return getImageData.apply(this, arguments);
            };
        """)
    
    def _save_session(self) -> None:
        """Save current session for reuse"""
        if not self.context:
            return
        
        try:
            # Get cookies and storage state
            storage_state = self.context.storage_state()
            
            # Save to file
            with open(self.session_file, 'wb') as f:
                pickle.dump({
                    'storage_state': storage_state,
                    'timestamp': random.randint(1000000000, 9999999999)  # Obfuscate timestamp
                }, f)
            
            print(f"✅ Session saved to {self.session_file}")
        except Exception as e:
            print(f"⚠️  Failed to save session: {e}")
    
    def _load_session(self) -> None:
        """Load previously saved session"""
        if not os.path.exists(self.session_file) or not self.context:
            return
        
        try:
            with open(self.session_file, 'rb') as f:
                session_data = pickle.load(f)
            
            # Restore storage state
            self.context.add_cookies(session_data['storage_state']['cookies'])
            
            # Set localStorage and sessionStorage if needed
            for origin in session_data['storage_state'].get('origins', []):
                if 'localStorage' in origin:
                    for item in origin['localStorage']:
                        self.page.evaluate(f"""
                            localStorage.setItem('{item['name']}', '{item['value']}');
                        """)
            
            print(f"✅ Session loaded from {self.session_file}")
        except Exception as e:
            print(f"⚠️  Failed to load session: {e}")
            # Remove corrupted session file
            try:
                os.remove(self.session_file)
            except:
                pass
    
    def save_session(self) -> None:
        """Public method to save session"""
        self._save_session()
    
    def human_delay(self, min_delay: Optional[float] = None, max_delay: Optional[float] = None) -> None:
        """Add human-like delay"""
        if min_delay is None:
            min_delay = self.config.delay_min
        if max_delay is None:
            max_delay = self.config.delay_max
        
        delay = random.uniform(min_delay, max_delay)
        self.page.wait_for_timeout(int(delay * 1000))
    
    def human_type(self, selector: str, text: str, delay_range: tuple = (50, 150)) -> None:
        """Type text with human-like delays"""
        element = self.page.locator(selector)
        element.click()
        
        # Clear existing text
        self.page.keyboard.press('Control+a')
        self.page.keyboard.press('Delete')
        
        # Type with random delays
        for char in text:
            self.page.keyboard.type(char)
            delay = random.uniform(delay_range[0], delay_range[1])
            self.page.wait_for_timeout(int(delay))
        
        # Random chance of making a "typo" and correcting it
        if random.random() < 0.05:  # 5% chance
            self.page.keyboard.type('x')
            self.page.wait_for_timeout(random.randint(100, 300))
            self.page.keyboard.press('Backspace')
    
    def human_click(self, selector: str, delay_before: tuple = (500, 1500), delay_after: tuple = (500, 1500)) -> None:
        """Click with human-like behavior"""
        # Delay before click
        delay = random.uniform(delay_before[0], delay_before[1])
        self.page.wait_for_timeout(int(delay))
        
        # Move mouse to element first (more realistic)
        element = self.page.locator(selector)
        element.hover()
        self.page.wait_for_timeout(random.randint(100, 300))
        
        # Click
        element.click()
        
        # Delay after click
        delay = random.uniform(delay_after[0], delay_after[1])
        self.page.wait_for_timeout(int(delay))
    
    def close(self) -> None:
        """Close browser and cleanup"""
        if self.context:
            self._save_session()
        
        if self.browser:
            self.browser.close()
        
        if self.playwright:
            self.playwright.stop()