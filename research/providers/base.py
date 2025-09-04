"""
Abstract base class for research providers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

class ResearchProvider(ABC):
    """Abstract base class for research providers"""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
    
    @abstractmethod
    def conduct_research(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Conduct research based on the provided prompt
        
        Args:
            prompt: The research prompt
            
        Returns:
            Dictionary containing research results with 'content' and optional 'search_results'
            or None if research fails
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate provider configuration"""
        pass