#!/usr/bin/env python3
"""デイリーリサーチ自動実行スクリプト"""

import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from web_automation import WebAutomation
from web_automation.config.settings import get_settings, setup_logging

logger = logging.getLogger(__name__)


def parse_arguments():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description="デイリーリサーチの自動実行")
    
    parser.add_argument(
        '--date', 
        type=str,
        help="対象日付 (YYYY-MM-DD形式。省略時は前日)"
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=9222,
        help="Chrome Remote Debuggingポート番号 (デフォルト: 9222)"
    )
    
    parser.add_argument(
        '--output-file',
        type=str,
        help="結果保存ファイル名（省略時は自動生成）"
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="実際に実行せずに設定内容のみ表示"
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help="設定ファイルのパス"
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help="ログレベル"
    )
    
    return parser.parse_args()


def get_target_date(date_str: str = None) -> datetime:
    """対象日付を取得
    
    Args:
        date_str: 日付文字列（YYYY-MM-DD形式）
        
    Returns:
        対象日付
    """
    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logger.error(f"日付形式が不正です: {date_str}")
            raise
    else:
        # 前日を返す
        return datetime.now() - timedelta(days=1)


def build_file_paths(settings, target_date: datetime):
    """ファイルパスを構築
    
    Args:
        settings: 設定オブジェクト
        target_date: 対象日付
        
    Returns:
        (template_path, diary_path, output_path)のタプル
    """
    # テンプレートパス
    template_path = settings.get_obsidian_template_path()
    
    # 日記パス
    diary_base = settings.get_obsidian_diary_base_path()
    diary_path = Path(diary_base) / str(target_date.year) / f"{target_date.month:02d}" / f"{target_date.strftime('%Y-%m-%d')}.md"
    
    # 出力パス
    output_dir = settings.get_output_dir()
    output_filename = f"research_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.md"
    output_path = Path(output_dir) / output_filename
    
    return str(template_path), str(diary_path), str(output_path)


def validate_paths(template_path: str, diary_path: str):
    """パスの検証
    
    Args:
        template_path: テンプレートファイルのパス
        diary_path: 日記ファイルのパス
        
    Returns:
        検証結果辞書
    """
    validation = {
        'template_exists': Path(template_path).exists(),
        'diary_exists': Path(diary_path).exists(),
        'template_path': template_path,
        'diary_path': diary_path
    }
    
    return validation


def execute_research(automation: WebAutomation, prompt: str, output_path: str) -> bool:
    """リサーチを実行
    
    Args:
        automation: WebAutomationインスタンス
        prompt: 生成されたプロンプト
        output_path: 結果保存パス
        
    Returns:
        実行成功の可否
    """
    try:
        with automation.connect() as browser:
            logger.info("Perplexityでリサーチを開始")
            
            # Perplexityサービスを取得
            perplexity = automation.service('perplexity')
            
            # 質問実行
            result = perplexity.ask_question(prompt)
            
            if result:
                # 結果を保存
                automation.save_result(result, output_path)
                logger.info(f"リサーチ結果保存完了: {output_path}")
                return True
            else:
                logger.error("リサーチ結果が空です")
                return False
                
    except Exception as e:
        logger.error(f"リサーチ実行エラー: {e}")
        return False


def main():
    """メイン処理"""
    try:
        # 引数解析
        args = parse_arguments()
        
        # 設定読み込み
        if args.config:
            from web_automation.config.settings import Settings
            settings = Settings(args.config)
        else:
            settings = get_settings()
        
        # ログレベル設定
        settings.set('logging.level', args.log_level)
        
        # ログ設定
        setup_logging(settings)
        
        logger.info("デイリーリサーチ開始")
        logger.info(f"引数: {vars(args)}")
        
        # 対象日付取得
        target_date = get_target_date(args.date)
        logger.info(f"対象日付: {target_date.strftime('%Y-%m-%d')}")
        
        # ファイルパス構築
        template_path, diary_path, output_path = build_file_paths(settings, target_date)
        
        # カスタム出力ファイル名
        if args.output_file:
            output_path = str(Path(settings.get_output_dir()) / args.output_file)
        
        logger.info(f"テンプレートパス: {template_path}")
        logger.info(f"日記パス: {diary_path}")
        logger.info(f"出力パス: {output_path}")
        
        # パス検証
        validation = validate_paths(template_path, diary_path)
        
        if not validation['template_exists']:
            logger.warning(f"テンプレートファイルが存在しません: {template_path}")
        
        if not validation['diary_exists']:
            logger.warning(f"日記ファイルが存在しません: {diary_path}")
        
        # Dry runの場合は設定内容のみ表示
        if args.dry_run:
            print("\n=== Dry Run Mode ===")
            print(f"対象日付: {target_date.strftime('%Y-%m-%d')}")
            print(f"テンプレートパス: {template_path} ({'存在' if validation['template_exists'] else '不存在'})")
            print(f"日記パス: {diary_path} ({'存在' if validation['diary_exists'] else '不存在'})")
            print(f"出力パス: {output_path}")
            print(f"Chromeポート: {args.port}")
            print("実行をスキップします")
            return
        
        # WebAutomationインスタンス作成
        automation = WebAutomation(port=args.port)
        
        # プロンプト構築
        logger.info("プロンプトを構築中...")
        prompt = automation.build_prompt(template_path, diary_path)
        
        logger.debug(f"生成されたプロンプト:\n{prompt}")
        
        # リサーチ実行
        success = execute_research(automation, prompt, output_path)
        
        if success:
            logger.info("デイリーリサーチが完了しました")
            print(f"結果は以下のファイルに保存されました: {output_path}")
        else:
            logger.error("デイリーリサーチが失敗しました")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("ユーザーによって中断されました")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()