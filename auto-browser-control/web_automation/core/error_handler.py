"""
Error Handler for Web Automation

Provides comprehensive error handling and retry logic with exponential backoff.
"""

import time
import logging
import functools
from typing import Callable, Any, Optional
from datetime import datetime


class ErrorHandler:
    """Handles errors and implements retry logic for web automation."""
    
    def __init__(self, max_retries=3, base_delay=1, max_delay=60):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)
    
    def handle_error(self, error: Exception, context: str = ""):
        """Handle and log errors."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_msg = f"[{timestamp}] Error in {context}: {type(error).__name__}: {str(error)}"
        self.logger.error(error_msg)
        return error_msg
    
    def log_error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def log_info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def retry_on_failure(self, 
                        max_retries: Optional[int] = None,
                        delay: Optional[float] = None,
                        exceptions: tuple = (Exception,)):
        """Decorator for automatic retry on failure."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                _max_retries = max_retries or self.max_retries
                _delay = delay or self.base_delay
                
                last_exception = None
                
                for attempt in range(_max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt < _max_retries:
                            retry_delay = self.calculate_delay(attempt) if delay is None else _delay
                            self.log_warning(
                                f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                                f"Retrying in {retry_delay:.1f} seconds..."
                            )
                            time.sleep(retry_delay)
                        else:
                            self.handle_error(e, f"{func.__name__} (final attempt)")
                            raise e
                
                # This should never be reached, but just in case
                if last_exception:
                    raise last_exception
                    
            return wrapper
        return decorator
    
    def safe_execute(self, 
                    func: Callable, 
                    *args, 
                    default_return=None,
                    context: str = "",
                    **kwargs) -> Any:
        """Safely execute a function and return default value on error."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.handle_error(e, context or func.__name__)
            return default_return
    
    def with_timeout(self, timeout_seconds: float):
        """Decorator to add timeout to function execution."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
                
                # Set up timeout signal (Unix only)
                try:
                    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(int(timeout_seconds))
                    
                    try:
                        result = func(*args, **kwargs)
                        return result
                    finally:
                        signal.alarm(0)
                        signal.signal(signal.SIGALRM, old_handler)
                        
                except (OSError, ValueError):
                    # Fallback for Windows or when signals aren't available
                    import threading
                    import time
                    
                    result = [None]
                    exception = [None]
                    
                    def target():
                        try:
                            result[0] = func(*args, **kwargs)
                        except Exception as e:
                            exception[0] = e
                    
                    thread = threading.Thread(target=target)
                    thread.daemon = True
                    thread.start()
                    thread.join(timeout_seconds)
                    
                    if thread.is_alive():
                        raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
                    
                    if exception[0]:
                        raise exception[0]
                    
                    return result[0]
                    
            return wrapper
        return decorator
    
    def batch_process(self, 
                     items: list, 
                     process_func: Callable, 
                     batch_size: int = 10,
                     continue_on_error: bool = True) -> list:
        """Process items in batches with error handling."""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            self.log_info(f"Processing batch {i//batch_size + 1} of {len(batch)} items")
            
            for item in batch:
                try:
                    result = process_func(item)
                    results.append(result)
                except Exception as e:
                    self.handle_error(e, f"Processing item {item}")
                    if not continue_on_error:
                        raise
                    results.append(None)  # Placeholder for failed item
            
            # Small delay between batches to avoid overwhelming services
            if i + batch_size < len(items):
                time.sleep(0.5)
        
        return results