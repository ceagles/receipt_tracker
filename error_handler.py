"""
Comprehensive error handling and rate limiting
"""

import time
import random
import logging
from typing import Callable, Any, Optional
from functools import wraps
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class RateLimiter:
    """Rate limiter to prevent overwhelming the server"""
    min_delay: float = 2.0
    max_delay: float = 8.0
    requests_per_minute: int = 10
    last_request_times: list = None
    
    def __post_init__(self):
        if self.last_request_times is None:
            self.last_request_times = []
    
    def wait_if_needed(self):
        """Wait if we're making requests too quickly"""
        now = time.time()
        
        # Remove requests older than 1 minute
        cutoff = now - 60
        self.last_request_times = [t for t in self.last_request_times if t > cutoff]
        
        # Check if we're at the rate limit
        if len(self.last_request_times) >= self.requests_per_minute:
            oldest_request = min(self.last_request_times)
            wait_time = 60 - (now - oldest_request)
            if wait_time > 0:
                print(f"⏰ Rate limit reached, waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
        
        # Add random human-like delay
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
        
        # Record this request
        self.last_request_times.append(now)


class CostcoScrapingError(Exception):
    """Base exception for Costco scraping errors"""
    pass


class AuthenticationError(CostcoScrapingError):
    """Authentication-related errors"""
    pass


class BotDetectionError(CostcoScrapingError):
    """Bot detection errors"""
    pass


class RateLimitError(CostcoScrapingError):
    """Rate limiting errors"""
    pass


class PageNavigationError(CostcoScrapingError):
    """Page navigation errors"""
    pass


class DataExtractionError(CostcoScrapingError):
    """Data extraction errors"""
    pass


def setup_logging(log_file: str = "receipt_tracker.log", level: str = "INFO") -> logging.Logger:
    """Setup comprehensive logging"""
    
    # Create logs directory
    import os
    os.makedirs("logs", exist_ok=True)
    log_path = f"logs/{log_file}"
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("receipt_tracker")
    logger.info("🚀 Receipt tracker logging initialized")
    
    return logger


def retry_on_failure(max_retries: int = 3, 
                    delay: float = 1.0, 
                    exponential_backoff: bool = True,
                    exceptions: tuple = (Exception,)):
    """Decorator for retrying functions on failure"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        break
                    
                    wait_time = delay
                    if exponential_backoff:
                        wait_time *= (2 ** attempt)
                    
                    # Add some randomness to avoid thundering herd
                    wait_time += random.uniform(0, wait_time * 0.1)
                    
                    print(f"⚠️  Attempt {attempt + 1} failed: {e}")
                    print(f"⏱️  Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    return decorator


def handle_bot_detection(func: Callable) -> Callable:
    """Decorator to handle bot detection gracefully"""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for bot detection indicators
            bot_indicators = [
                'captcha',
                'bot detected',
                'automated',
                'suspicious activity',
                'rate limit',
                'too many requests',
                'blocked',
                'access denied'
            ]
            
            if any(indicator in error_msg for indicator in bot_indicators):
                print("🤖 Bot detection triggered!")
                print("💡 Recommendations:")
                print("   1. Wait 5-10 minutes before trying again")
                print("   2. Use a different IP address or VPN")
                print("   3. Clear browser sessions and cookies")
                print("   4. Try during off-peak hours")
                
                raise BotDetectionError(f"Bot detection triggered: {e}")
            
            raise e
    
    return wrapper


def safe_page_operation(timeout: int = 30):
    """Decorator for safe page operations with timeout"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                elapsed = time.time() - start_time
                
                if elapsed >= timeout:
                    raise PageNavigationError(f"Operation timed out after {timeout}s: {e}")
                
                # Check for common page errors
                error_msg = str(e).lower()
                
                if 'timeout' in error_msg:
                    raise PageNavigationError(f"Page operation timeout: {e}")
                elif 'not found' in error_msg or 'element not found' in error_msg:
                    raise DataExtractionError(f"Required element not found: {e}")
                elif 'navigation' in error_msg:
                    raise PageNavigationError(f"Navigation failed: {e}")
                
                raise e
        
        return wrapper
    return decorator


class ErrorRecovery:
    """Handles error recovery strategies"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_counts = {}
        self.last_error_time = {}
    
    def record_error(self, error_type: str, error: Exception):
        """Record an error for tracking"""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_error_time[error_type] = datetime.now()
        
        self.logger.error(f"Error recorded - {error_type}: {error}")
    
    def should_continue(self, error_type: str, max_errors: int = 5, time_window: int = 300) -> bool:
        """Check if we should continue after errors"""
        error_count = self.error_counts.get(error_type, 0)
        last_error = self.last_error_time.get(error_type)
        
        if error_count >= max_errors:
            if last_error and (datetime.now() - last_error).seconds < time_window:
                self.logger.error(f"Too many {error_type} errors ({error_count}) in {time_window}s")
                return False
        
        return True
    
    def reset_error_count(self, error_type: str):
        """Reset error count for a specific type"""
        self.error_counts[error_type] = 0
        if error_type in self.last_error_time:
            del self.last_error_time[error_type]


def emergency_stop_check():
    """Check for emergency stop conditions"""
    stop_file = "EMERGENCY_STOP"
    
    if os.path.exists(stop_file):
        print("🛑 Emergency stop file detected!")
        print("   Remove 'EMERGENCY_STOP' file to continue")
        raise CostcoScrapingError("Emergency stop activated")


def monitor_memory_usage():
    """Monitor memory usage and warn if getting high"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        if memory.percent > 85:
            print(f"⚠️  High memory usage: {memory.percent:.1f}%")
            
        if memory.percent > 95:
            print("🔥 Critical memory usage - stopping to prevent system issues")
            raise CostcoScrapingError("Critical memory usage detected")
            
    except ImportError:
        # psutil not available, skip monitoring
        pass


# Rate limiter instance for global use
global_rate_limiter = RateLimiter()


def with_rate_limiting(func: Callable) -> Callable:
    """Decorator to add rate limiting to functions"""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        global_rate_limiter.wait_if_needed()
        return func(*args, **kwargs)
    
    return wrapper