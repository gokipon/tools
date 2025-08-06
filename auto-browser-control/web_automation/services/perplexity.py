"""Perplexity専用操作クラス"""

import time
import logging
from typing import Optional, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_service import BaseService
from ..utils.element_helper import ElementHelper
from ..utils.wait_helper import WaitHelper

logger = logging.getLogger(__name__)


class PerplexityService(BaseService):
    """Perplexity専用操作"""
    
    # Perplexityの要素セレクタ
    SELECTORS = {
        'search_input': 'textarea[placeholder*="質問"],textarea[placeholder*="Ask"],input[placeholder*="質問"],input[placeholder*="Ask"]',
        'search_button': 'button[type="submit"],button[aria-label*="送信"],button[aria-label*="Submit"]',
        'result_container': '.prose,.answer,.response,article',
        'loading_indicator': '.loading,.spinner,[data-loading="true"]',
        'research_mode_button': 'button[value="research"][role="radio"],button.segmented-control[value="research"]'
    }
    
    def __init__(self, browser_manager):
        super().__init__(browser_manager)
        self.element_helper = ElementHelper()
        self.wait_helper = WaitHelper()
    
    def get_service_url(self) -> str:
        """PerplexityのURL"""
        return "https://www.perplexity.ai"
    
    def ask_question(self, question: str, wait_timeout: int = 60) -> str:
        """質問を投稿して回答を取得
        
        Args:
            question: 質問文
            wait_timeout: 回答待機タイムアウト(秒)
            
        Returns:
            回答テキスト
        """
        try:
            # Perplexityページに移動
            self.navigate_to_service()
            time.sleep(2)
            
            # リサーチモードに切り替え
            self._switch_to_research_mode()
            
            # 質問入力
            self._input_question(question)
            
            # 検索実行
            self._submit_question()
            
            # 回答待機・取得
            answer = self._wait_for_answer(wait_timeout)
            
            logger.info("Perplexity質問・回答取得完了")
            return answer
            
        except Exception as e:
            logger.error(f"Perplexity操作エラー: {e}")
            raise
    
    def _switch_to_research_mode(self) -> None:
        """リサーチモードに切り替える"""
        try:
            # リサーチモードボタンを探す
            research_button = self.element_helper.find_element_with_fallbacks(
                self.driver,
                [
                    'button[value="research"][role="radio"]',
                    'button.segmented-control[value="research"]',
                    'button[role="radio"][aria-checked="false"][value="research"]',
                    '.segmented-control button[value="research"]'
                ]
            )
            
            if research_button:
                # ボタンがすでに選択されているかチェック
                is_selected = research_button.get_attribute("aria-checked") == "true"
                
                if not is_selected:
                    # JavaScriptでクリックして確実に実行
                    self.driver.execute_script("arguments[0].click();", research_button)
                    logger.info("リサーチモードに切り替えました")
                    time.sleep(1)  # モード切り替え後の待機
                else:
                    logger.info("すでにリサーチモードが選択されています")
            else:
                logger.warning("リサーチモードボタンが見つかりません")
                
        except Exception as e:
            logger.warning(f"リサーチモード切り替えエラー (継続): {e}")
            # エラーが発生しても処理を継続（モード切り替えは必須ではない）
    
    def _input_question(self, question: str) -> None:
        """質問をテキストエリアに入力"""
        try:
            # 複数のセレクタを試行
            input_element = self.element_helper.find_element_with_fallbacks(
                self.driver, 
                [
                    'textarea[placeholder*="質問"]',
                    'textarea[placeholder*="Ask"]', 
                    'textarea',
                    'input[type="text"]',
                    '[contenteditable="true"]'
                ]
            )
            
            if not input_element:
                raise NoSuchElementException("質問入力フィールドが見つかりません")
            
            # 既存のテキストをクリア
            input_element.clear()
            time.sleep(0.5)
            
            # 質問を入力
            input_element.send_keys(question)
            time.sleep(1)
            
            logger.info("質問入力完了")
            
        except Exception as e:
            logger.error(f"質問入力エラー: {e}")
            raise
    
    def _submit_question(self) -> None:
        """質問を送信"""
        try:
            # 送信ボタンを探す
            submit_button = self.element_helper.find_element_with_fallbacks(
                self.driver,
                [
                    'button[type="submit"]',
                    'button[aria-label*="送信"]',
                    'button[aria-label*="Submit"]',
                    'button:contains("送信")',
                    'button:contains("Submit")',
                    'button:contains("Ask")'
                ]
            )
            
            if submit_button:
                self.driver.execute_script("arguments[0].click();", submit_button)
                logger.info("送信ボタンクリック")
            else:
                # Enterキーで送信を試行
                input_element = self.driver.find_element(By.TAG_NAME, "textarea")
                input_element.send_keys(Keys.RETURN)
                logger.info("Enterキーで送信")
            
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"質問送信エラー: {e}")
            raise
    
    def _wait_for_answer(self, timeout: int) -> str:
        """回答の表示を待機して取得
        
        Args:
            timeout: 待機タイムアウト(秒)
            
        Returns:
            回答テキスト
        """
        try:
            # ローディングが終わるまで待機
            self._wait_for_loading_complete(timeout // 2)
            
            # 回答要素の出現を待機
            answer_element = self.wait_helper.wait_for_element_appear(
                self.driver,
                [
                    '.prose',
                    '.answer',
                    '.response', 
                    'article',
                    '[role="main"] div',
                    'main div'
                ],
                timeout=timeout
            )
            
            if not answer_element:
                raise TimeoutException("回答が表示されませんでした")
            
            # 回答テキストを取得
            answer_text = self._extract_answer_text(answer_element)
            
            logger.info("回答取得完了")
            return answer_text
            
        except Exception as e:
            logger.error(f"回答取得エラー: {e}")
            raise
    
    def _wait_for_loading_complete(self, timeout: int) -> None:
        """ローディングの完了を待機"""
        try:
            loading_selectors = [
                '.loading',
                '.spinner', 
                '[data-loading="true"]',
                '.animate-spin'
            ]
            
            for selector in loading_selectors:
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
                    )
                except TimeoutException:
                    continue
            
            # 追加の待機時間
            time.sleep(3)
            
        except Exception as e:
            logger.warning(f"ローディング待機エラー: {e}")
    
    def _extract_answer_text(self, element) -> str:
        """回答要素からテキストを抽出
        
        Args:
            element: 回答要素
            
        Returns:
            回答テキスト
        """
        try:
            # まずは直接テキストを取得
            text = element.get_attribute('textContent') or element.text
            
            if text and len(text.strip()) > 10:
                return text.strip()
            
            # 子要素からテキストを収集
            paragraphs = element.find_elements(By.CSS_SELECTOR, "p, div, span")
            text_parts = []
            
            for p in paragraphs:
                p_text = p.text.strip()
                if p_text and p_text not in text_parts:
                    text_parts.append(p_text)
            
            if text_parts:
                return "\n\n".join(text_parts)
            
            # フォールバック: ページの主要コンテンツを取得
            return self.driver.execute_script("""
                let mainContent = document.querySelector('main, [role="main"], .main-content');
                return mainContent ? mainContent.innerText : document.body.innerText;
            """)
            
        except Exception as e:
            logger.error(f"テキスト抽出エラー: {e}")
            return "回答の取得に失敗しました"