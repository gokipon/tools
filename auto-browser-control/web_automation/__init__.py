"""
Web Automation Library for Browser Control

A comprehensive library for automating web browsers using Chrome Remote Debugging Protocol.
Designed for Obsidian integration and automated research workflows.
"""

from .core.browser_manager import BrowserManager
from .core.prompt_builder import PromptBuilder
from .core.error_handler import ErrorHandler

__version__ = "1.0.0"
__all__ = ["BrowserManager", "PromptBuilder", "ErrorHandler", "WebAutomation"]


class WebAutomation:
    """Main entry point for web automation functionality."""
    
    def __init__(self, port=9222, headless=False):
        self.browser_manager = BrowserManager(port=port, headless=headless)
        self.prompt_builder = PromptBuilder()
        self.error_handler = ErrorHandler()
    
    def connect(self):
        """Connect to Chrome browser."""
        return self.browser_manager.connect()
    
    def build_prompt(self, template_path, diary_path):
        """Build prompt from Obsidian template and diary files."""
        return self.prompt_builder.build_from_files(template_path, diary_path)
    
    def service(self, service_name):
        """Get a service instance."""
        if service_name == 'perplexity':
            from .services.perplexity import PerplexityService
            return PerplexityService(self.browser_manager)
        elif service_name == 'gmail':
            from .services.gmail import GmailService
            return GmailService(self.browser_manager)
        elif service_name == 'github':
            from .services.github import GitHubService
            return GitHubService(self.browser_manager)
        else:
            from .services.generic import GenericService
            return GenericService(self.browser_manager)
    
    def save_result(self, result, filename):
        """Save automation result to file."""
        import os
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = os.path.expanduser("~/automation_results")
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, f"{timestamp}_{filename}")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Automation Result - {timestamp}\n\n")
            f.write(result)
        
        return filepath