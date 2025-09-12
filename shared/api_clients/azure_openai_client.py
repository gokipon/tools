#!/usr/bin/env python3
"""
Azure OpenAI 統一クライアント

全ワークフローで共有されるAzure OpenAI APIクライアント
"""

from typing import List, Dict, Optional, Any
import time
from openai import OpenAI

from ..config_loader import get_config
from ..utils.logger_setup import LoggerMixin


class AzureOpenAIClient(LoggerMixin):
    """Azure OpenAI API統一クライアント"""
    
    def __init__(self, custom_config: Optional[Dict[str, str]] = None):
        """
        クライアントを初期化
        
        Args:
            custom_config: カスタム設定（Noneの場合は共通設定を使用）
        """
        super().__init__()
        config = get_config()
        
        if custom_config:
            self.config = custom_config
        else:
            self.config = config.get_azure_openai_config()
        
        self.client = self._init_openai_client()
        self.conversation_history = []
        self.api_delay = float(config.get('API_DELAY', 2))
        self.max_retries = int(config.get('MAX_RETRIES', 3))
    
    def _init_openai_client(self) -> OpenAI:
        """OpenAI クライアントを初期化"""
        try:
            return OpenAI(
                api_key=self.config['api_key'],
                base_url=self.config['base_url']
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            raise
    
    def generate_completion(self, 
                          messages: List[Dict[str, str]], 
                          model: Optional[str] = None,
                          temperature: float = 1.0,
                          max_tokens: Optional[int] = None,
                          maintain_history: bool = False) -> Optional[str]:
        """
        チャット完了APIを呼び出し
        
        Args:
            messages: メッセージリスト
            model: 使用するモデル（Noneの場合はデフォルト）
            temperature: 温度パラメータ
            max_tokens: 最大トークン数
            maintain_history: 会話履歴を維持するか
            
        Returns:
            生成されたテキスト
        """
        if model is None:
            model = self.config['deployment']
        
        try:
            # 会話履歴を維持する場合
            if maintain_history:
                self.conversation_history.extend(messages)
                use_messages = self.conversation_history
            else:
                use_messages = messages
            
            # API呼び出しパラメータ
            params = {
                'model': model,
                'messages': use_messages,
                'temperature': temperature
            }
            
            if max_tokens:
                params['max_tokens'] = max_tokens
            
            # リトライ機能付きでAPI呼び出し
            for attempt in range(self.max_retries):
                try:
                    self.logger.debug(f"API call attempt {attempt + 1}/{self.max_retries}")
                    
                    response = self.client.chat.completions.create(**params)
                    
                    content = response.choices[0].message.content
                    
                    # 会話履歴を維持する場合はアシスタントの応答を追加
                    if maintain_history and content:
                        self.conversation_history.append({
                            'role': 'assistant',
                            'content': content
                        })
                    
                    # API制限対応の待機
                    if self.api_delay > 0:
                        time.sleep(self.api_delay)
                    
                    self.logger.debug("API call successful")
                    return content
                
                except Exception as e:
                    self.logger.warning(f"API call attempt {attempt + 1} failed: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)  # 指数バックオフ
                    else:
                        raise
            
            return None
        
        except Exception as e:
            self.logger.error(f"Failed to generate completion: {e}")
            raise
    
    def generate_with_system_prompt(self,
                                  system_prompt: str,
                                  user_message: str,
                                  **kwargs) -> Optional[str]:
        """
        システムプロンプト付きで生成
        
        Args:
            system_prompt: システムプロンプト
            user_message: ユーザーメッセージ
            **kwargs: generate_completionの追加引数
            
        Returns:
            生成されたテキスト
        """
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message}
        ]
        
        return self.generate_completion(messages, **kwargs)
    
    def continue_conversation(self, user_message: str, **kwargs) -> Optional[str]:
        """
        会話を継続（履歴を維持）
        
        Args:
            user_message: ユーザーメッセージ
            **kwargs: generate_completionの追加引数
            
        Returns:
            生成されたテキスト
        """
        messages = [{'role': 'user', 'content': user_message}]
        return self.generate_completion(messages, maintain_history=True, **kwargs)
    
    def reset_conversation(self):
        """会話履歴をリセット"""
        self.conversation_history = []
        self.logger.debug("Conversation history reset")
    
    def add_system_message(self, system_message: str):
        """システムメッセージを会話履歴に追加"""
        self.conversation_history.append({
            'role': 'system',
            'content': system_message
        })
        self.logger.debug("System message added to conversation history")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """現在の会話履歴を取得"""
        return self.conversation_history.copy()


# よく使われる設定での便利関数
def create_azure_client() -> AzureOpenAIClient:
    """デフォルト設定でAzure OpenAIクライアントを作成"""
    return AzureOpenAIClient()


def generate_radio_script(prompt_template: str, research_report: str) -> Optional[str]:
    """ラジオ台本生成用の便利関数"""
    client = create_azure_client()
    
    system_prompt = "あなたは経験豊富なラジオ番組制作者です。レポートを基に魅力的なラジオトーク台本を章ごとに作成します。"
    user_message = f"{prompt_template}\n\nレポート:\n{research_report}"
    
    return client.generate_with_system_prompt(system_prompt, user_message)


def generate_research_content(query: str, context: str = "") -> Optional[str]:
    """リサーチ内容生成用の便利関数"""
    client = create_azure_client()
    
    system_prompt = "あなたは詳細で正確なリサーチを行う専門家です。与えられたクエリについて包括的な情報を提供してください。"
    user_message = f"クエリ: {query}\n\n追加コンテキスト:\n{context}" if context else f"クエリ: {query}"
    
    return client.generate_with_system_prompt(system_prompt, user_message)