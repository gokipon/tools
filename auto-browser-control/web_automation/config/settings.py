"""
Configuration Management

Handles settings loading from JSON files and environment variables.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class Settings:
    """Configuration settings manager."""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file
        self.settings = {}
        self.load_settings()
    
    def load_settings(self):
        """Load settings from config file and environment variables."""
        # Default settings
        self.settings = {
            'browser': {
                'port': 9222,
                'headless': False,
                'timeout': 30,
                'user_data_dir': '/tmp/chrome-selenium-debug'
            },
            'obsidian': {
                'vault_path': '~/Documents/Obsidian Vault',
                'daily_notes_format': '%Y-%m-%d',
                'daily_notes_path': 'daily',
                'templates_path': 'templates'
            },
            'automation': {
                'results_dir': '~/automation_results',
                'screenshot_dir': '~/automation_screenshots',
                'max_retries': 3,
                'base_delay': 1,
                'max_delay': 60
            },
            'services': {
                'perplexity': {
                    'base_url': 'https://www.perplexity.ai',
                    'response_timeout': 60
                },
                'gmail': {
                    'base_url': 'https://mail.google.com'
                },
                'github': {
                    'base_url': 'https://github.com'
                }
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }
        
        # Load from config file if specified
        if self.config_file:
            self.load_from_file(self.config_file)
        else:
            # Try to load from default locations
            default_locations = [
                'auto_browser_config.json',
                '~/.auto_browser_config.json',
                '~/.config/auto_browser_control/config.json'
            ]
            
            for location in default_locations:
                if self.load_from_file(location):
                    break
        
        # Override with environment variables
        self.load_from_env()
    
    def load_from_file(self, file_path: str) -> bool:
        """Load settings from JSON file."""
        try:
            path = Path(file_path).expanduser().resolve()
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    file_settings = json.load(f)
                    self._merge_settings(file_settings)
                return True
        except Exception:
            pass
        return False
    
    def load_from_env(self):
        """Load settings from environment variables."""
        env_mappings = {
            'CHROME_DEBUG_PORT': ('browser', 'port'),
            'CHROME_HEADLESS': ('browser', 'headless'),
            'CHROME_TIMEOUT': ('browser', 'timeout'),
            'OBSIDIAN_VAULT_PATH': ('obsidian', 'vault_path'),
            'AUTOMATION_RESULTS_DIR': ('automation', 'results_dir'),
            'MAX_RETRIES': ('automation', 'max_retries'),
            'PERPLEXITY_TIMEOUT': ('services', 'perplexity', 'response_timeout'),
            'LOG_LEVEL': ('logging', 'level')
        }
        
        for env_var, setting_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_setting(setting_path, self._convert_env_value(value))
    
    def _merge_settings(self, new_settings: Dict[str, Any]):
        """Recursively merge new settings into existing settings."""
        for key, value in new_settings.items():
            if key in self.settings and isinstance(self.settings[key], dict) and isinstance(value, dict):
                self._merge_settings_recursive(self.settings[key], value)
            else:
                self.settings[key] = value
    
    def _merge_settings_recursive(self, existing: Dict, new: Dict):
        """Recursively merge dictionaries."""
        for key, value in new.items():
            if key in existing and isinstance(existing[key], dict) and isinstance(value, dict):
                self._merge_settings_recursive(existing[key], value)
            else:
                existing[key] = value
    
    def _set_nested_setting(self, path: tuple, value: Any):
        """Set a nested setting value using a tuple path."""
        current = self.settings
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Try boolean
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        elif value.lower() in ('false', '0', 'no', 'off'):
            return False
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def get(self, *path, default=None) -> Any:
        """Get a setting value using dot notation."""
        current = self.settings
        
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def set(self, *path, value: Any):
        """Set a setting value using dot notation."""
        if len(path) == 0:
            return
        
        current = self.settings
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[path[-1]] = value
    
    def save_to_file(self, file_path: str = None):
        """Save current settings to JSON file."""
        if not file_path:
            file_path = self.config_file or 'auto_browser_config.json'
        
        try:
            path = Path(file_path).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception:
            return False
    
    def get_chrome_options(self) -> Dict[str, Any]:
        """Get Chrome browser options."""
        return {
            'port': self.get('browser', 'port', default=9222),
            'headless': self.get('browser', 'headless', default=False),
            'timeout': self.get('browser', 'timeout', default=30),
            'user_data_dir': self.get('browser', 'user_data_dir', default='/tmp/chrome-selenium-debug')
        }
    
    def get_obsidian_config(self) -> Dict[str, Any]:
        """Get Obsidian configuration."""
        return {
            'vault_path': self.get('obsidian', 'vault_path', default='~/Documents/Obsidian Vault'),
            'daily_notes_format': self.get('obsidian', 'daily_notes_format', default='%Y-%m-%d'),
            'daily_notes_path': self.get('obsidian', 'daily_notes_path', default='daily'),
            'templates_path': self.get('obsidian', 'templates_path', default='templates')
        }
    
    def get_automation_config(self) -> Dict[str, Any]:
        """Get automation configuration."""
        return {
            'results_dir': self.get('automation', 'results_dir', default='~/automation_results'),
            'screenshot_dir': self.get('automation', 'screenshot_dir', default='~/automation_screenshots'),
            'max_retries': self.get('automation', 'max_retries', default=3),
            'base_delay': self.get('automation', 'base_delay', default=1),
            'max_delay': self.get('automation', 'max_delay', default=60)
        }
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service."""
        return self.get('services', service_name, default={})
    
    def expand_path(self, path: str) -> str:
        """Expand user path and resolve."""
        return str(Path(path).expanduser().resolve())
    
    def create_sample_config(self, file_path: str = 'auto_browser_config.json'):
        """Create a sample configuration file."""
        sample_config = {
            "browser": {
                "port": 9222,
                "headless": False,
                "timeout": 30,
                "user_data_dir": "/tmp/chrome-selenium-debug"
            },
            "obsidian": {
                "vault_path": "~/Documents/Obsidian Vault",
                "daily_notes_format": "%Y-%m-%d",
                "daily_notes_path": "daily",
                "templates_path": "templates"
            },
            "automation": {
                "results_dir": "~/automation_results",
                "screenshot_dir": "~/automation_screenshots",
                "max_retries": 3,
                "base_delay": 1,
                "max_delay": 60
            },
            "services": {
                "perplexity": {
                    "base_url": "https://www.perplexity.ai",
                    "response_timeout": 60
                },
                "gmail": {
                    "base_url": "https://mail.google.com"
                },
                "github": {
                    "base_url": "https://github.com"
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
        
        try:
            path = Path(file_path).expanduser().resolve()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f, indent=2, ensure_ascii=False)
            return str(path)
        except Exception:
            return None


# Global settings instance
_settings = None

def get_settings(config_file: str = None) -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None or config_file:
        _settings = Settings(config_file)
    return _settings

def reload_settings(config_file: str = None):
    """Reload settings from file."""
    global _settings
    _settings = Settings(config_file)