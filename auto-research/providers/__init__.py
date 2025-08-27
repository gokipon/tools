"""
Provider package for auto-research system
"""

from .base import ResearchProvider
from .perplexity_provider import PerplexityProvider

try:
    from .langchain_provider import LangChainProvider
except ImportError:
    # LangChain dependencies not installed yet
    LangChainProvider = None

__all__ = ['ResearchProvider', 'PerplexityProvider', 'LangChainProvider']