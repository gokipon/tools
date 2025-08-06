"""汎用操作クラス"""

import time
import logging
from typing import List, Optional, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_service import BaseService
from ..utils.element_helper import ElementHelper
from ..utils.wait_helper import WaitHelper

logger = logging.getLogger(__name__)


class GenericService(BaseService):
    """汎用Web操作"""
    
    def get_service_url(self) -> str:
        """汎用サービスなのでURLは動的"""
        return ""
    
    def __init__(self, browser_manager):
        super().__init__(browser_manager)
        self.element_helper = ElementHelper()
        self.wait_helper = WaitHelper()
    
    def navigate(self, url: str) -> None:
        """指定URLに移動
        
        Args:
            url: 移動先URL
        """
        try:
            self.driver.get(url)
            time.sleep(2)
            logger.info(f"ページ移動完了: {url}")
        except Exception as e:
            logger.error(f"ページ移動エラー: {e}")
            raise
    
    def input_text(self, selector: str, text: str, clear: bool = True) -> bool:
        """テキストを入力
        
        Args:
            selector: 要素のセレクタ
            text: 入力テキスト
            clear: 既存テキストをクリアするか
            
        Returns:
            入力成功の可否
        """
        try:
            element = self.wait_helper.wait_for_element_clickable(
                self.driver, selector, timeout=10
            )
            
            if not element:
                raise NoSuchElementException(f"要素が見つかりません: {selector}")
            
            if clear:
                element.clear()
                time.sleep(0.5)
            
            element.send_keys(text)
            time.sleep(0.5)
            
            logger.info(f"テキスト入力完了: {selector}")
            return True
            
        except Exception as e:
            logger.error(f"テキスト入力エラー ({selector}): {e}")
            return False
    
    def click_button(self, selector: str) -> bool:
        """ボタンをクリック
        
        Args:
            selector: ボタンのセレクタ
            
        Returns:
            クリック成功の可否
        """
        try:
            element = self.wait_helper.wait_for_element_clickable(
                self.driver, selector, timeout=10
            )
            
            if not element:
                raise NoSuchElementException(f"ボタンが見つかりません: {selector}")
            
            # JavaScriptクリックを試行（要素が隠れている場合）
            try:
                element.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", element)
            
            time.sleep(1)
            logger.info(f"ボタンクリック完了: {selector}")
            return True
            
        except Exception as e:
            logger.error(f"ボタンクリックエラー ({selector}): {e}")
            return False
    
    def wait_for_elements(self, selector: str, timeout: int = 10) -> List:
        """要素の出現を待機して複数取得
        
        Args:
            selector: 要素のセレクタ
            timeout: 待機タイムアウト
            
        Returns:
            見つかった要素のリスト
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
            )
            
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            logger.info(f"{len(elements)}個の要素を取得: {selector}")
            return elements
            
        except TimeoutException:
            logger.warning(f"要素が見つかりません: {selector}")
            return []
        except Exception as e:
            logger.error(f"要素取得エラー ({selector}): {e}")
            return []
    
    def get_text(self, selector: str) -> str:
        """要素のテキストを取得
        
        Args:
            selector: 要素のセレクタ
            
        Returns:
            要素のテキスト
        """
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            text = element.text or element.get_attribute('textContent')
            logger.info(f"テキスト取得完了: {selector}")
            return text.strip()
            
        except NoSuchElementException:
            logger.warning(f"要素が見つかりません: {selector}")
            return ""
        except Exception as e:
            logger.error(f"テキスト取得エラー ({selector}): {e}")
            return ""
    
    def get_attribute(self, selector: str, attribute: str) -> str:
        """要素の属性値を取得
        
        Args:
            selector: 要素のセレクタ
            attribute: 属性名
            
        Returns:
            属性値
        """
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            value = element.get_attribute(attribute)
            logger.info(f"属性取得完了: {selector}@{attribute}")
            return value or ""
            
        except NoSuchElementException:
            logger.warning(f"要素が見つかりません: {selector}")
            return ""
        except Exception as e:
            logger.error(f"属性取得エラー ({selector}@{attribute}): {e}")
            return ""
    
    def execute_script(self, script: str, *args) -> Any:
        """JavaScriptを実行
        
        Args:
            script: JavaScriptコード
            *args: スクリプトの引数
            
        Returns:
            スクリプトの実行結果
        """
        try:
            result = self.driver.execute_script(script, *args)
            logger.info("JavaScript実行完了")
            return result
            
        except Exception as e:
            logger.error(f"JavaScript実行エラー: {e}")
            return None
    
    def scroll_to_element(self, selector: str) -> bool:
        """要素までスクロール
        
        Args:
            selector: 要素のセレクタ
            
        Returns:
            スクロール成功の可否
        """
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                element
            )
            time.sleep(1)
            logger.info(f"スクロール完了: {selector}")
            return True
            
        except Exception as e:
            logger.error(f"スクロールエラー ({selector}): {e}")
            return False
    
    def take_screenshot(self, filename: Optional[str] = None) -> str:
        """スクリーンショットを撮影
        
        Args:
            filename: 保存ファイル名（指定しない場合は自動生成）
            
        Returns:
            保存されたファイル名
        """
        try:
            if not filename:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            self.driver.save_screenshot(filename)
            logger.info(f"スクリーンショット保存: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"スクリーンショットエラー: {e}")
            return ""