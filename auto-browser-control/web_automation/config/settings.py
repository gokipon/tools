"""設定ファイル"""

import os
from typing import Optional, Dict, Any
from pathlib import Path


class Settings:
    """アプリケーション設定"""
    
    # デフォルト設定（アプリケーション動作設定のみ）
    DEFAULT_CONFIG = {
        "chrome": {
            "remote_debugging_port": 9222,
            "startup_timeout": 10
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
    
    def __init__(self, config_file: Optional[str] = None, env_file: Optional[str] = None):
        """
        Args:
            config_file: 設定ファイルのパス
            env_file: 環境変数ファイルのパス（.env）
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        # .envファイルがある場合は読み込み
        self._load_env_file(env_file)
        
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
        
        # 環境変数からオーバーライド
        self._load_from_env()
        
        # 必須環境変数の検証
        self._validate_required_env()
    
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
    
    def _load_env_file(self, env_file: Optional[str] = None) -> None:
        """環境変数ファイル（.env）を読み込み
        
        Args:
            env_file: .envファイルのパス（Noneの場合は.envを自動検索）
        """
        if env_file is None:
            # カレントディレクトリの.envファイルを探す
            env_file = ".env"
        
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        # コメント行や空行をスキップ
                        if not line or line.startswith('#'):
                            continue
                        
                        # KEY=VALUE形式を解析
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # クォートを除去
                            if (value.startswith('"') and value.endswith('"')) or \
                               (value.startswith("'") and value.endswith("'")):
                                value = value[1:-1]
                            
                            # 既存の環境変数がない場合のみ設定
                            if key and not os.getenv(key):
                                os.environ[key] = value
                        else:
                            print(f"Warning: Invalid line format in {env_file}:{line_num}: {line}")
                            
            except Exception as e:
                print(f".envファイル読み込みエラー: {e}")
    
    def _load_from_env(self) -> None:
        """環境変数から設定をロード（マシン固有・機密情報）"""
        # Chrome設定（マシン固有）
        if os.getenv("CHROME_DEBUG_PORT"):
            self.config["chrome"]["remote_debugging_port"] = int(os.getenv("CHROME_DEBUG_PORT"))
        
        if os.getenv("CHROME_USER_DATA_DIR"):
            if "chrome" not in self.config:
                self.config["chrome"] = {}
            self.config["chrome"]["user_data_dir"] = os.getenv("CHROME_USER_DATA_DIR")
        
        # パス設定（マシン固有）
        if "paths" not in self.config:
            self.config["paths"] = {}
            
        # 必須のマシン固有パス
        if os.getenv("OBSIDIAN_BASE_PATH"):
            self.config["paths"]["obsidian_base"] = os.getenv("OBSIDIAN_BASE_PATH")
        else:
            # デフォルト値は提供しない（環境変数での設定を強制）
            self.config["paths"]["obsidian_base"] = None
        
        if os.getenv("TEMPLATE_FILE"):
            self.config["paths"]["template_file"] = os.getenv("TEMPLATE_FILE")
        else:
            self.config["paths"]["template_file"] = "knowledge/llm-usecase/デイリーリサーチ.md"
        
        if os.getenv("DIARY_BASE"):
            self.config["paths"]["diary_base"] = os.getenv("DIARY_BASE")
        else:
            self.config["paths"]["diary_base"] = "diary"
        
        if os.getenv("OUTPUT_DIR"):
            self.config["paths"]["output_dir"] = os.getenv("OUTPUT_DIR")
        else:
            self.config["paths"]["output_dir"] = "./output"
        
        if not os.getenv("CHROME_USER_DATA_DIR"):
            self.config["chrome"]["user_data_dir"] = "/tmp/chrome-selenium-debug"
    
    def _validate_required_env(self) -> None:
        """必須環境変数の検証"""
        required_vars = {
            "OBSIDIAN_BASE_PATH": "Obsidianのベースディレクトリパス"
        }
        
        missing_vars = []
        for var_name, description in required_vars.items():
            if not os.getenv(var_name):
                missing_vars.append(f"{var_name} ({description})")
        
        if missing_vars:
            error_msg = f"必須環境変数が設定されていません:\n" + "\n".join(f"  - {var}" for var in missing_vars)
            error_msg += "\n\n.envファイルまたはシステム環境変数で設定してください。"
            raise ValueError(error_msg)
    
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