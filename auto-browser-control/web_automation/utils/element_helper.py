"""要素操作ヘルパー"""

import time
import logging
from typing import List, Optional, Union
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException

logger = logging.getLogger(__name__)


class ElementHelper:
    """要素操作のヘルパークラス"""
    
    @staticmethod
    def find_element_with_fallbacks(
        driver: webdriver.Chrome, 
        selectors: List[str]
    ) -> Optional[WebElement]:
        """複数のセレクタで要素を検索（フォールバック付き）
        
        Args:
            driver: WebDriverインスタンス
            selectors: 試行するセレクタのリスト
            
        Returns:
            見つかった要素（見つからない場合はNone）
        """
        for selector in selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if element and element.is_displayed():
                    logger.debug(f"要素発見 (セレクタ: {selector})")
                    return element
            except NoSuchElementException:
                continue
        
        logger.warning(f"要素が見つかりません（試行セレクタ: {selectors}）")
        return None
    
    @staticmethod
    def find_elements_with_fallbacks(
        driver: webdriver.Chrome,
        selectors: List[str]
    ) -> List[WebElement]:
        """複数のセレクタで要素を複数検索
        
        Args:
            driver: WebDriverインスタンス
            selectors: 試行するセレクタのリスト
            
        Returns:
            見つかった要素のリスト
        """
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.debug(f"{len(elements)}個の要素発見 (セレクタ: {selector})")
                    return elements
            except Exception:
                continue
        
        logger.warning(f"要素が見つかりません（試行セレクタ: {selectors}）")
        return []
    
    @staticmethod
    def safe_click(element: WebElement, driver: webdriver.Chrome) -> bool:
        """安全なクリック実行（複数手法を試行）
        
        Args:
            element: クリック対象の要素
            driver: WebDriverインスタンス
            
        Returns:
            クリック成功の可否
        """
        click_methods = [
            lambda: element.click(),
            lambda: driver.execute_script("arguments[0].click();", element),
            lambda: driver.execute_script("arguments[0].dispatchEvent(new Event('click'));", element)
        ]
        
        for i, method in enumerate(click_methods, 1):
            try:
                method()
                logger.debug(f"クリック成功 (手法{i})")
                time.sleep(0.5)
                return True
            except Exception as e:
                logger.debug(f"クリック手法{i}失敗: {e}")
                continue
        
        logger.error("すべてのクリック手法が失敗しました")
        return False
    
    @staticmethod
    def safe_input(element: WebElement, text: str, clear: bool = True) -> bool:
        """安全なテキスト入力
        
        Args:
            element: 入力対象の要素
            text: 入力テキスト
            clear: 既存テキストをクリアするか
            
        Returns:
            入力成功の可否
        """
        try:
            if clear:
                element.clear()
                time.sleep(0.3)
            
            # 段階的に入力（長いテキストの場合）
            chunk_size = 100
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                element.send_keys(chunk)
                time.sleep(0.1)
            
            logger.debug("テキスト入力成功")
            return True
            
        except Exception as e:
            logger.error(f"テキスト入力エラー: {e}")
            return False
    
    @staticmethod
    def is_element_visible(element: WebElement) -> bool:
        """要素の可視性確認
        
        Args:
            element: 確認対象の要素
            
        Returns:
            可視かどうか
        """
        try:
            return element.is_displayed() and element.is_enabled()
        except Exception:
            return False
    
    @staticmethod
    def get_element_text_safe(element: WebElement) -> str:
        """安全な要素テキスト取得
        
        Args:
            element: テキスト取得対象の要素
            
        Returns:
            要素のテキスト
        """
        try:
            # 複数の手法でテキストを取得
            text = element.text
            if text:
                return text.strip()
            
            text = element.get_attribute('textContent')
            if text:
                return text.strip()
            
            text = element.get_attribute('innerText')
            if text:
                return text.strip()
            
            text = element.get_attribute('value')
            if text:
                return text.strip()
            
            return ""
            
        except Exception as e:
            logger.debug(f"テキスト取得エラー: {e}")
            return ""
    
    @staticmethod
    def scroll_to_element_safe(
        driver: webdriver.Chrome, 
        element: WebElement,
        align_to_top: bool = False
    ) -> bool:
        """安全な要素へのスクロール
        
        Args:
            driver: WebDriverインスタンス
            element: スクロール対象の要素
            align_to_top: 要素を画面上部に配置するか
            
        Returns:
            スクロール成功の可否
        """
        try:
            if align_to_top:
                driver.execute_script(
                    "arguments[0].scrollIntoView(true);", 
                    element
                )
            else:
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                    element
                )
            
            time.sleep(1)
            logger.debug("要素へのスクロール成功")
            return True
            
        except Exception as e:
            logger.error(f"スクロールエラー: {e}")
            return False
    
    @staticmethod
    def wait_for_element_stable(
        element: WebElement,
        timeout: float = 5.0,
        check_interval: float = 0.5
    ) -> bool:
        """要素の安定化を待機（位置・サイズの変化がなくなるまで）
        
        Args:
            element: 確認対象の要素
            timeout: 最大待機時間
            check_interval: チェック間隔
            
        Returns:
            安定化したかどうか
        """
        try:
            import time
            start_time = time.time()
            last_location = None
            last_size = None
            stable_count = 0
            
            while time.time() - start_time < timeout:
                try:
                    current_location = element.location
                    current_size = element.size
                    
                    if (last_location == current_location and 
                        last_size == current_size):
                        stable_count += 1
                        if stable_count >= 3:  # 3回連続で同じなら安定
                            return True
                    else:
                        stable_count = 0
                    
                    last_location = current_location
                    last_size = current_size
                    time.sleep(check_interval)
                    
                except Exception:
                    return False
            
            return False
            
        except Exception:
            return False