"""
Perplexity API provider for research
"""

import requests
import json
from typing import Dict, Any, Optional, List
import logging

from .base import ResearchProvider

class PerplexityProvider(ResearchProvider):
    """Perplexity API research provider"""
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "perplexity"
    
    def get_required_config_keys(self) -> List[str]:
        """Get required config keys"""
        return ['PERPLEXITY_API_KEY']
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        api_key = self.config.get('PERPLEXITY_API_KEY')
        if not api_key:
            self.logger.error("PERPLEXITY_API_KEY not found in config")
            return False
        return True
    
    def conduct_research(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Conduct research using Perplexity API
        
        Args:
            prompt: Research prompt
            
        Returns:
            Dict with 'content' and 'search_results', or None if failed
        """
        if not self.validate_config():
            return None
            
        api_key = self.config.get('PERPLEXITY_API_KEY')
        url = "https://api.perplexity.ai/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "sonar-deep-research",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "reasoning_effort": "medium",
            "temperature": 0.7,
            "max_tokens": 8192
        }
        
        try:
            self.logger.info("Calling Perplexity API...")
            response = requests.post(url, headers=headers, json=data, timeout=1200)
            response.raise_for_status()
            
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                search_results = result.get('search_results', [])
                return {'content': content, 'search_results': search_results}
            else:
                self.logger.error("Unexpected API response format")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Perplexity API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            return None