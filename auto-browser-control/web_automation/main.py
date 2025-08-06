"""メインAPIクラス"""

from contextlib import contextmanager
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from .core.browser_manager import BrowserManager
from .core.prompt_builder import PromptBuilder
from .services.base_service import ServiceFactory

logger = logging.getLogger(__name__)


class WebAutomation:
    """Web自動化のメインAPIクラス"""
    
    def __init__(self, port: int = 9222, user_data_dir: Optional[str] = None):
        """
        Args:
            port: Chrome Remote Debuggingポート番号
            user_data_dir: Chromeのユーザーデータディレクトリ
        """
        self.browser_manager = BrowserManager(port=port, user_data_dir=user_data_dir)
        self.prompt_builder = PromptBuilder()
        self.service_factory = ServiceFactory()
    
    @contextmanager
    def connect(self):
        """ブラウザ接続のコンテキストマネージャー"""
        driver = None
        try:
            driver = self.browser_manager.connect()
            logger.info("ブラウザ接続成功")
            yield driver
        except Exception as e:
            logger.error(f"ブラウザ操作エラー: {e}")
            raise
        finally:
            if driver:
                self.browser_manager.disconnect(driver)
                logger.info("ブラウザ接続終了")
    
    def build_prompt(self, template_path: str, diary_path: str) -> str:
        """プロンプトを構築する
        
        Args:
            template_path: テンプレートファイルのパス
            diary_path: 日記ファイルのパス
            
        Returns:
            結合されたプロンプト文字列
        """
        return self.prompt_builder.build_prompt(template_path, diary_path)
    
    def service(self, service_name: str) -> Any:
        """サービス固有の操作クラスを取得
        
        Args:
            service_name: サービス名 ('perplexity', 'gmail', 'github', 'generic')
            
        Returns:
            サービス操作クラスのインスタンス
        """
        return self.service_factory.get_service(service_name, self.browser_manager)
    
    def save_result(self, content: str, filename: str) -> None:
        """実行結果をファイルに保存
        
        Args:
            content: 保存する内容
            filename: ファイル名
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"結果をファイルに保存: {filename}")
        except Exception as e:
            logger.error(f"ファイル保存エラー: {e}")
            raise