"""サービス基底クラスとファクトリ"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from selenium import webdriver

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """サービス操作の基底クラス"""
    
    def __init__(self, browser_manager):
        """
        Args:
            browser_manager: BrowserManagerインスタンス
        """
        self.browser_manager = browser_manager
        self._driver: Optional[webdriver.Chrome] = None
    
    @property
    def driver(self) -> webdriver.Chrome:
        """WebDriverインスタンスを取得"""
        if self._driver is None:
            self._driver = self.browser_manager.connect()
        return self._driver
    
    @abstractmethod
    def get_service_url(self) -> str:
        """サービスのURLを取得"""
        pass
    
    def navigate_to_service(self) -> None:
        """サービスページに移動"""
        url = self.get_service_url()
        self.driver.get(url)
        logger.info(f"サービスページに移動: {url}")
    
    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        if self._driver:
            self.browser_manager.disconnect(self._driver)
            self._driver = None


class ServiceFactory:
    """サービスクラスのファクトリ"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
    
    def get_service(self, service_name: str, browser_manager) -> BaseService:
        """サービスインスタンスを取得
        
        Args:
            service_name: サービス名
            browser_manager: BrowserManagerインスタンス
            
        Returns:
            サービスインスタンス
        """
        if service_name in self._services:
            return self._services[service_name]
        
        # 動的インポートでサービスクラスを取得
        service_class = self._get_service_class(service_name)
        service_instance = service_class(browser_manager)
        
        self._services[service_name] = service_instance
        return service_instance
    
    def _get_service_class(self, service_name: str) -> type:
        """サービス名からクラスを取得
        
        Args:
            service_name: サービス名
            
        Returns:
            サービスクラス
        """
        service_map = {
            'perplexity': 'PerplexityService',
            'gmail': 'GmailService', 
            'github': 'GitHubService',
            'generic': 'GenericService'
        }
        
        if service_name not in service_map:
            raise ValueError(f"サポートされていないサービス: {service_name}")
        
        class_name = service_map[service_name]
        module_name = f"web_automation.services.{service_name}"
        
        try:
            module = __import__(module_name, fromlist=[class_name])
            service_class = getattr(module, class_name)
            return service_class
        except (ImportError, AttributeError) as e:
            logger.error(f"サービスクラス取得エラー ({service_name}): {e}")
            raise ImportError(f"サービス '{service_name}' が見つかりません")