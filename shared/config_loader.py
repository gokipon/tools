#!/usr/bin/env python3
"""
統一設定ローダー - 全ワークフローで使用される共通設定管理

環境変数ベースの設定を統一的に読み込み、デフォルト値とバリデーションを提供
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging


class ConfigError(Exception):
    """設定関連のエラー"""
    pass


class CommonConfig:
    """統一設定管理クラス"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        設定を初期化
        
        Args:
            project_root: プロジェクトルートディレクトリ（自動検出される）
        """
        self.project_root = project_root or self._find_project_root()
        self.env_file = self.project_root / ".env"
        self._config_cache = {}
        self._load_env_file()
    
    def _find_project_root(self) -> Path:
        """プロジェクトルートディレクトリを自動検出"""
        current = Path(__file__).parent
        while current.parent != current:
            if (current / ".env").exists():
                return current
            current = current.parent
        
        # fallback
        return Path(__file__).parent.parent
    
    def _load_env_file(self):
        """環境変数ファイルを読み込み"""
        if not self.env_file.exists():
            logging.warning(f"Environment file not found: {self.env_file}")
            return
        
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 空行やコメント行をスキップ
                    if not line or line.startswith('#'):
                        continue
                    
                    # KEY=VALUE形式をチェック
                    if '=' not in line:
                        continue
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')  # クォートを除去
                    
                    # 環境変数の展開を行う（${VAR}形式）
                    import re
                    def expand_var(match):
                        var_name = match.group(1)
                        return os.environ.get(var_name, match.group(0))
                    
                    value = re.sub(r'\$\{([^}]+)\}', expand_var, value)
                    
                    # 環境変数として設定（既存の環境変数を優先）
                    if key not in os.environ:
                        os.environ[key] = value
        
        except Exception as e:
            logging.error(f"Failed to load environment file {self.env_file}: {e}")
    
    def get(self, key: str, default: Any = None, required: bool = False) -> Any:
        """
        設定値を取得
        
        Args:
            key: 設定キー
            default: デフォルト値
            required: 必須フラグ
            
        Returns:
            設定値
            
        Raises:
            ConfigError: 必須設定が見つからない場合
        """
        value = os.environ.get(key, default)
        
        if required and value is None:
            raise ConfigError(f"Required configuration '{key}' not found")
        
        return value
    
    def get_path(self, key: str, default: Optional[str] = None, required: bool = False) -> Optional[Path]:
        """
        パス設定を取得してPathオブジェクトで返す
        
        Args:
            key: 設定キー
            default: デフォルト値
            required: 必須フラグ
            
        Returns:
            Pathオブジェクト
        """
        value = self.get(key, default, required)
        return Path(value) if value else None
    
    def get_azure_openai_config(self) -> Dict[str, str]:
        """Azure OpenAI設定を取得"""
        return {
            'api_key': self.get('AZURE_OPENAI_API_KEY', required=True),
            'base_url': self.get('AZURE_OPENAI_BASE_URL', required=True),
            'deployment': self.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o'),
            'api_version': self.get('AZURE_OPENAI_API_VERSION', '2025-04-01-preview'),
        }
    
    def get_perplexity_config(self) -> Dict[str, str]:
        """Perplexity設定を取得"""
        return {
            'api_key': self.get('PERPLEXITY_API_KEY', required=True),
            'model': self.get('PERPLEXITY_MODEL', 'llama-3.1-sonar-small-128k-online'),
        }
    
    def get_line_config(self) -> Dict[str, str]:
        """LINE Notify設定を取得"""
        return {
            'token': self.get('LINE_NOTIFY_TOKEN'),
            'api_url': self.get('LINE_NOTIFY_API_URL', 'https://notify-api.line.me/api/notify'),
        }
    
    def get_obsidian_config(self) -> Dict[str, Any]:
        """Obsidian設定を取得"""
        return {
            'vault_path': self.get_path('OBSIDIAN_VAULT_PATH', required=True),
            'user_info_path': self.get_path('USER_INFO_PATH', required=True),
            'research_report_path': self.get_path('RESEARCH_REPORT_PATH', required=True),
            'radio_output_path': self.get_path('RADIO_OUTPUT_PATH'),
        }
    
    def validate_required_keys(self, keys: List[str]) -> bool:
        """
        必須キーが設定されているかチェック
        
        Args:
            keys: チェックするキーのリスト
            
        Returns:
            全て設定されている場合True
            
        Raises:
            ConfigError: 必須設定が見つからない場合
        """
        missing = []
        for key in keys:
            if not os.environ.get(key):
                missing.append(key)
        
        if missing:
            raise ConfigError(f"Missing required configuration keys: {', '.join(missing)}")
        
        return True
    
    def get_log_config(self) -> Dict[str, Any]:
        """ログ設定を取得"""
        return {
            'level': self.get('LOG_LEVEL', 'INFO').upper(),
            'format': self.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            'timezone': self.get('TIMEZONE', 'Asia/Tokyo'),
        }


# グローバル設定インスタンス
_global_config = None

def get_config() -> CommonConfig:
    """グローバル設定インスタンスを取得"""
    global _global_config
    if _global_config is None:
        _global_config = CommonConfig()
    return _global_config


# よく使われる設定の便利関数
def get_azure_openai_config() -> Dict[str, str]:
    """Azure OpenAI設定を取得"""
    return get_config().get_azure_openai_config()

def get_perplexity_config() -> Dict[str, str]:
    """Perplexity設定を取得"""
    return get_config().get_perplexity_config()

def get_obsidian_config() -> Dict[str, Any]:
    """Obsidian設定を取得"""
    return get_config().get_obsidian_config()