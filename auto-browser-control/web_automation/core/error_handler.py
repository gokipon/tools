"""エラーハンドリングモジュール"""

import time
import logging
from typing import Callable, Any, Type
from selenium.common.exceptions import (
    WebDriverException, 
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException
)

logger = logging.getLogger(__name__)


class ErrorHandler:
    """エラーハンドリングとリトライ処理"""
    
    RETRYABLE_EXCEPTIONS = (
        WebDriverException,
        TimeoutException,
        NoSuchElementException,
        ElementClickInterceptedException
    )
    
    def retry_operation(
        self, 
        operation: Callable, 
        max_retries: int = 3,
        delay: float = 2.0,
        backoff_factor: float = 1.5
    ) -> Any:
        """操作をリトライ実行
        
        Args:
            operation: 実行する操作
            max_retries: 最大リトライ回数
            delay: 初期待機時間
            backoff_factor: 待機時間の増加率
            
        Returns:
            操作の結果
            
        Raises:
            最後のエラー
        """
        last_exception = None
        current_delay = delay
        
        for attempt in range(max_retries + 1):
            try:
                return operation()
                
            except self.RETRYABLE_EXCEPTIONS as e:
                last_exception = e
                
                if attempt < max_retries:
                    logger.warning(
                        f"操作失敗 (試行 {attempt + 1}/{max_retries + 1}): {e}"
                    )
                    logger.info(f"{current_delay}秒待機後、再試行します")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                else:
                    logger.error(f"最大リトライ回数に達しました: {e}")
                    
            except Exception as e:
                # リトライ対象外のエラーは即座に再発生
                logger.error(f"リトライ不可能なエラー: {e}")
                raise e
        
        # 最後のエラーを再発生
        if last_exception:
            raise last_exception
    
    def handle_element_error(self, element_selector: str, error: Exception) -> None:
        """要素操作エラーの処理
        
        Args:
            element_selector: 要素のセレクタ
            error: 発生したエラー
        """
        if isinstance(error, NoSuchElementException):
            logger.error(f"要素が見つかりません: {element_selector}")
        elif isinstance(error, ElementClickInterceptedException):
            logger.error(f"要素がクリックできません: {element_selector}")
        elif isinstance(error, TimeoutException):
            logger.error(f"要素の待機がタイムアウトしました: {element_selector}")
        else:
            logger.error(f"要素操作エラー ({element_selector}): {error}")
    
    def handle_network_error(self, url: str, error: Exception) -> None:
        """ネットワークエラーの処理
        
        Args:
            url: アクセス先のURL
            error: 発生したエラー
        """
        logger.error(f"ネットワークエラー ({url}): {error}")
        
    def create_error_context(self, operation_name: str, **context) -> dict:
        """エラー文脈情報の作成
        
        Args:
            operation_name: 操作名
            **context: 追加の文脈情報
            
        Returns:
            エラー文脈辞書
        """
        return {
            "operation": operation_name,
            "timestamp": time.time(),
            **context
        }