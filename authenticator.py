"""
Advanced Costco authentication with anti-detection
"""

import random
import time
from typing import Optional, Tuple
from dataclasses import dataclass

from browser_manager import BrowserManager
from config import Config


@dataclass
class AuthResult:
    """Result of authentication attempt"""
    success: bool
    message: str
    requires_2fa: bool = False
    session_saved: bool = False


class CostcoAuthenticator:
    """Advanced Costco authenticator with human-like behavior"""
    
    def __init__(self, browser_manager: BrowserManager, config: Config):
        self.browser = browser_manager
        self.config = config
        self.login_url = "https://www.costco.com/LogonForm"
        self.orders_url = "https://www.costco.com/myaccount/#/app/4900eb1f-0c10-4bd9-99c3-c59e6c1ecebf/ordersandpurchases"
    
    def login(self, username: str, password: str) -> AuthResult:
        """
        Perform login with advanced anti-detection techniques
        """
        print("🔐 Starting Costco login process...")
        
        for attempt in range(1, self.config.max_retries + 1):
            print(f"🔄 Login attempt {attempt}/{self.config.max_retries}")
            
            try:
                result = self._attempt_login(username, password, attempt)
                if result.success:
                    print("✅ Login successful!")
                    self.browser.save_session()
                    result.session_saved = True
                    return result
                elif result.requires_2fa:
                    print("🔐 2FA required - manual intervention needed")
                    return result
                else:
                    print(f"❌ Login attempt {attempt} failed: {result.message}")
                    if attempt < self.config.max_retries:
                        delay = random.uniform(3, 8) * attempt  # Exponential backoff
                        print(f"⏱️  Waiting {delay:.1f} seconds before retry...")
                        time.sleep(delay)
            
            except Exception as e:
                print(f"❌ Login attempt {attempt} error: {e}")
                if attempt < self.config.max_retries:
                    time.sleep(random.uniform(5, 10))
        
        return AuthResult(False, f"Login failed after {self.config.max_retries} attempts")
    
    def _attempt_login(self, username: str, password: str, attempt: int) -> AuthResult:
        """Perform a single login attempt"""
        
        # Navigate to login page with realistic behavior
        print("📱 Navigating to Costco login page...")
        self.browser.page.goto(self.login_url, wait_until='domcontentloaded')
        
        # Random delay to simulate reading the page
        self.browser.human_delay(2, 5)
        
        # Check if already logged in
        if self._is_logged_in():
            return AuthResult(True, "Already logged in")
        
        # Look for and handle any popups/modals
        self._handle_popups()
        
        # Find and fill login form
        login_result = self._fill_login_form(username, password)
        if not login_result:
            return AuthResult(False, "Could not find or fill login form")
        
        # Submit form and wait for response
        submit_result = self._submit_login_form()
        if not submit_result:
            return AuthResult(False, "Failed to submit login form")
        
        # Check login result
        return self._check_login_result()
    
    def _fill_login_form(self, username: str, password: str) -> bool:
        """Fill login form with human-like behavior"""
        print("📝 Filling login form...")
        
        try:
            # Wait for form to be ready
            self.browser.page.wait_for_selector('input[type="email"], input[name="logonId"], input[id="signInName"]', timeout=10000)
            
            # Find email field with multiple selectors
            email_selectors = [
                'input[type="email"]',
                'input[name="logonId"]', 
                'input[id="signInName"]',
                'input[autocomplete="email"]',
                'input[autocomplete="username"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="username" i]'
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    if self.browser.page.locator(selector).is_visible():
                        email_field = selector
                        break
                except:
                    continue
            
            if not email_field:
                print("❌ Could not find email input field")
                return False
            
            # Fill email with human-like typing
            print(f"✏️  Typing username into field: {email_field}")
            self.browser.human_type(email_field, username)
            
            # Random delay before password
            self.browser.human_delay(0.5, 2)
            
            # Find password field
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id="password"]',
                'input[autocomplete="current-password"]'
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    if self.browser.page.locator(selector).is_visible():
                        password_field = selector
                        break
                except:
                    continue
            
            if not password_field:
                print("❌ Could not find password input field")
                return False
            
            # Fill password with human-like typing
            print(f"🔒 Typing password into field: {password_field}")
            self.browser.human_type(password_field, password)
            
            # Random delay after filling form
            self.browser.human_delay(1, 3)
            
            return True
            
        except Exception as e:
            print(f"❌ Error filling login form: {e}")
            return False
    
    def _submit_login_form(self) -> bool:
        """Submit login form"""
        print("🚀 Submitting login form...")
        
        try:
            # Look for submit button
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Sign In")',
                'button:has-text("Log In")',
                'button:has-text("Continue")',
                '.signin-button',
                '#signInBtn'
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    if self.browser.page.locator(selector).is_visible():
                        print(f"🖱️  Clicking submit button: {selector}")
                        self.browser.human_click(selector)
                        submitted = True
                        break
                except:
                    continue
            
            # Fallback: press Enter on password field
            if not submitted:
                print("🔄 Fallback: pressing Enter on password field")
                self.browser.page.keyboard.press('Enter')
            
            # Wait for page to respond
            print("⏳ Waiting for login response...")
            self.browser.page.wait_for_timeout(3000)
            
            return True
            
        except Exception as e:
            print(f"❌ Error submitting form: {e}")
            return False
    
    def _check_login_result(self) -> AuthResult:
        """Check if login was successful"""
        print("🔍 Checking login result...")
        
        # Wait for page to load
        time.sleep(3)
        
        # Check current URL
        current_url = self.browser.page.url
        print(f"📍 Current URL: {current_url}")
        
        # Check for error messages
        error_indicators = [
            '.error',
            '.alert-danger',
            '.field-validation-error',
            '[role="alert"]',
            '.invalid-feedback'
        ]
        
        for selector in error_indicators:
            try:
                if self.browser.page.locator(selector).is_visible():
                    error_text = self.browser.page.locator(selector).inner_text()
                    print(f"❌ Error message found: {error_text}")
                    return AuthResult(False, f"Login error: {error_text}")
            except:
                continue
        
        # Check for 2FA indicators
        tfa_indicators = [
            'input[placeholder*="code" i]',
            'input[placeholder*="verification" i]',
            ':has-text("verification code")',
            ':has-text("two-factor")',
            ':has-text("authenticator")'
        ]
        
        for selector in tfa_indicators:
            try:
                if self.browser.page.locator(selector).is_visible():
                    print("🔐 2FA verification required")
                    return AuthResult(False, "2FA verification required", requires_2fa=True)
            except:
                continue
        
        # Check if we're still on login page
        if 'login' in current_url.lower() or 'signin' in current_url.lower() or 'logon' in current_url.lower():
            # Look for any form fields that suggest we're still on login page
            login_fields = self.browser.page.locator('input[type="email"], input[type="password"], input[name="logonId"]')
            if login_fields.count() > 0:
                print("❌ Still on login page - credentials may be incorrect")
                return AuthResult(False, "Still on login page after submission")
        
        # Check for successful login indicators
        success_indicators = [
            ':has-text("Welcome")',
            ':has-text("My Account")',
            ':has-text("Sign Out")',
            ':has-text("Logout")',
            '.user-info',
            '.account-info'
        ]
        
        for selector in success_indicators:
            try:
                if self.browser.page.locator(selector).is_visible():
                    print("✅ Login success indicator found")
                    return AuthResult(True, "Login successful")
            except:
                continue
        
        # If we made it here, assume success if we're not on login page
        if not any(term in current_url.lower() for term in ['login', 'signin', 'logon']):
            print("✅ Login appears successful - redirected away from login page")
            return AuthResult(True, "Login successful - redirected")
        
        return AuthResult(False, "Login status unclear")
    
    def _is_logged_in(self) -> bool:
        """Check if already logged in"""
        success_indicators = [
            ':has-text("Sign Out")',
            ':has-text("My Account")',
            '.user-info'
        ]
        
        for selector in success_indicators:
            try:
                if self.browser.page.locator(selector).is_visible():
                    return True
            except:
                continue
        return False
    
    def _handle_popups(self) -> None:
        """Handle any popups or modals that might appear"""
        popup_selectors = [
            'button:has-text("Close")',
            'button:has-text("Dismiss")', 
            'button:has-text("No Thanks")',
            '.modal-close',
            '.popup-close',
            '[aria-label="Close"]'
        ]
        
        for selector in popup_selectors:
            try:
                if self.browser.page.locator(selector).is_visible():
                    print(f"🔲 Closing popup: {selector}")
                    self.browser.page.locator(selector).click()
                    self.browser.human_delay(0.5, 1.5)
            except:
                continue
    
    def navigate_to_orders(self) -> bool:
        """Navigate to orders page after successful login"""
        print("📦 Navigating to orders page...")
        
        try:
            self.browser.page.goto(self.orders_url, wait_until='domcontentloaded')
            self.browser.human_delay(3, 6)
            
            # Check if we made it to orders page
            if 'ordersandpurchases' in self.browser.page.url.lower():
                print("✅ Successfully navigated to orders page")
                return True
            else:
                print(f"❌ Failed to reach orders page. Current URL: {self.browser.page.url}")
                return False
                
        except Exception as e:
            print(f"❌ Error navigating to orders: {e}")
            return False
    
    def find_warehouse_tab(self) -> bool:
        """Find and click the warehouse tab"""
        print("🏪 Looking for warehouse tab...")
        
        # Wait for page to load
        self.browser.human_delay(2, 4)
        
        # Look for warehouse tab indicators
        warehouse_selectors = [
            ':has-text("Warehouse")',
            ':has-text("In-Store")', 
            ':has-text("Receipt")',
            '[role="tab"]:has-text("Warehouse")',
            'button:has-text("Warehouse")',
            'a:has-text("Warehouse")'
        ]
        
        for selector in warehouse_selectors:
            try:
                if self.browser.page.locator(selector).is_visible():
                    print(f"🎯 Found warehouse tab: {selector}")
                    self.browser.human_click(selector)
                    self.browser.human_delay(2, 4)
                    return True
            except:
                continue
        
        # If no specific warehouse tab found, look for any tabs and try the second one
        try:
            tabs = self.browser.page.locator('[role="tab"]')
            if tabs.count() >= 2:
                print("🔄 Trying second tab (likely warehouse)")
                tabs.nth(1).click()
                self.browser.human_delay(2, 4)
                return True
        except:
            pass
        
        print("❌ Could not find warehouse tab")
        return False