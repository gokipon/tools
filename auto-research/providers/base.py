"""
Abstract base class for research providers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

class ResearchProvider(ABC):
    """Abstract base class for research providers"""
    
    def __init__(self, config: Dict[str, str], logger: logging.Logger):
        """
        Initialize the research provider
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
    
    @abstractmethod
    def conduct_research(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Conduct research based on the given prompt
        
        Args:
            prompt: Research prompt
            
        Returns:
            Research result dict with 'content' and optional 'search_results',
            or None if research failed
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of this provider
        
        Returns:
            Provider name string
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate that the required configuration is present
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    def get_required_config_keys(self) -> List[str]:
        """
        Get list of required configuration keys for this provider
        
        Returns:
            List of required config key names
        """
        return []