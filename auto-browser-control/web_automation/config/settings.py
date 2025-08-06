"""設定ファイル"""

import os
from typing import Optional, Dict, Any
from pathlib import Path


class Settings:
    """アプリケーション設定"""
    
    # デフォルト設定
    DEFAULT_CONFIG = {
        "chrome": {
            "remote_debugging_port": 9222,
            "user_data_dir": "/tmp/chrome-selenium-debug",
            "startup_timeout": 10
        },
        "paths": {
            "obsidian_base": "/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am",
            "template_file": "knowledge/llm-usecase/デイリーリサーチ.md",
            "diary_base": "diary",
            "output_dir": "output"
        },
        "automation": {
            "default_timeout": 30,
            "retry_count": 3,
            "retry_delay": 2.0
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "web_automation.log"
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Args:
            config_file: 設定ファイルのパス
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
        
        # 環境変数からオーバーライド
        self._load_from_env()
    
    def load_from_file(self, config_file: str) -> None:
        """設定ファイルから読み込み
        
        Args:
            config_file: 設定ファイルのパス
        """
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # ディープマージ
            self._deep_merge(self.config, file_config)
            
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
    
    def _load_from_env(self) -> None:
        """環境変数から設定をロード"""
        # Chrome設定
        if os.getenv("CHROME_DEBUG_PORT"):
            self.config["chrome"]["remote_debugging_port"] = int(os.getenv("CHROME_DEBUG_PORT"))
        
        if os.getenv("CHROME_USER_DATA_DIR"):
            self.config["chrome"]["user_data_dir"] = os.getenv("CHROME_USER_DATA_DIR")
        
        # Obsidianパス
        if os.getenv("OBSIDIAN_BASE_PATH"):
            self.config["paths"]["obsidian_base"] = os.getenv("OBSIDIAN_BASE_PATH")
        
        if os.getenv("TEMPLATE_FILE"):
            self.config["paths"]["template_file"] = os.getenv("TEMPLATE_FILE")
        
        # 出力ディレクトリ
        if os.getenv("OUTPUT_DIR"):
            self.config["paths"]["output_dir"] = os.getenv("OUTPUT_DIR")
    
    def _deep_merge(self, base_dict: Dict, update_dict: Dict) -> None:
        """辞書のディープマージ"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """ドット記法でキーを取得
        
        Args:
            key_path: "chrome.remote_debugging_port" のようなキーパス
            default: デフォルト値
            
        Returns:
            設定値
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """ドット記法でキーを設定
        
        Args:
            key_path: キーパス
            value: 設定する値
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_obsidian_template_path(self) -> str:
        """Obsidianテンプレートファイルの完全パスを取得"""
        base = self.get("paths.obsidian_base")
        template = self.get("paths.template_file")
        return os.path.join(base, template)
    
    def get_obsidian_diary_base_path(self) -> str:
        """Obsidian日記ディレクトリの完全パスを取得"""
        base = self.get("paths.obsidian_base")
        diary_base = self.get("paths.diary_base")
        return os.path.join(base, diary_base)
    
    def get_output_dir(self) -> str:
        """出力ディレクトリのパスを取得（存在しない場合は作成）"""
        output_dir = self.get("paths.output_dir")
        
        # 相対パスの場合は絶対パスに変換
        if not os.path.isabs(output_dir):
            output_dir = os.path.abspath(output_dir)
        
        # ディレクトリが存在しない場合は作成
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        return output_dir
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書として取得"""
        return self.config.copy()
    
    def save_to_file(self, config_file: str) -> None:
        """設定をファイルに保存
        
        Args:
            config_file: 保存先ファイルパス
        """
        try:
            import json
            
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")


# グローバル設定インスタンス
settings = Settings()


def get_settings() -> Settings:
    """グローバル設定インスタンスを取得"""
    return settings


def setup_logging(settings_instance: Optional[Settings] = None) -> None:
    """ログ設定のセットアップ"""
    import logging
    
    if settings_instance is None:
        settings_instance = settings
    
    log_level = settings_instance.get("logging.level", "INFO")
    log_format = settings_instance.get("logging.format")
    log_file = settings_instance.get("logging.file")
    
    # ログレベル変換
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    level = level_map.get(log_level.upper(), logging.INFO)
    
    # ログ設定
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )