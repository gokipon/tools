"""
Provider factory for creating research providers
"""

from typing import Dict, Any
import logging
from .base import ResearchProvider
from .perplexity_provider import PerplexityProvider
from .langchain_provider import LangChainProvider

class ProviderFactory:
    """Factory for creating research providers"""
    
    @staticmethod
    def create_provider(provider_type: str, config: Dict[str, Any], logger: logging.Logger) -> ResearchProvider:
        """
        Create a research provider instance
        
        Args:
            provider_type: Type of provider ('perplexity' or 'langchain')
            config: Configuration dictionary
            logger: Logger instance
            
        Returns:
            ResearchProvider instance
            
        Raises:
            ValueError: If provider type is unknown
        """
        provider_type = provider_type.lower()
        
        if provider_type == "perplexity":
            return PerplexityProvider(config, logger)
        elif provider_type == "langchain":
            return LangChainProvider(config, logger)
        else:
            available_providers = ["perplexity", "langchain"]
            raise ValueError(f"Unknown provider: {provider_type}. Available providers: {available_providers}")
    
    @staticmethod
    def get_available_providers() -> list:
        """Get list of available providers"""
        return ["perplexity", "langchain"]