# Auto Research System - Provider Pattern Implementation

Provider パターンによる拡張可能自動リサーチシステム

## 概要

既存のPerplexity APIベースの自動リサーチシステムを、Provider パターンを使用して拡張可能なアーキテクチャに改修しました。Perplexity APIとLangChain（Azure OpenAI）をコマンドで切り替え可能で、段階的にLangChain Open Deep Research原理を適用してPhD レベルの研究深度を目指します。

## 実装状況

### ✅ Phase 1: Provider パターン基盤構築 (完了)

- **Provider パターン実装**: 拡張可能なアーキテクチャ構築
- **後方互換性100%維持**: 既存スクリプトは無変更で動作
- **コマンドライン拡張**: Provider選択、設定ファイル指定、デバッグモード
- **階層的設定管理**: CLI > provider.env > .env > default

### 🔄 Phase 2-4: 段階実装予定

- **Phase 2**: Azure OpenAI基本統合
- **Phase 3**: 検索API統合 (Tavily)
- **Phase 4**: マルチエージェント協調機能

## 使用方法

### 基本的な使用方法（後方互換性）

```bash
# 既存の方法（デフォルト: Perplexity）
python auto_research.py
```

### Provider指定

```bash
# Perplexity APIを明示的に指定
python auto_research.py --provider perplexity

# LangChain Provider（Phase 2-4で段階実装）
python auto_research.py --provider langchain
```

### オプション指定

```bash
# 設定ファイル指定
python auto_research.py --provider langchain --config custom.env

# デバッグモード
python auto_research.py --debug

# Provider一覧表示
python auto_research.py --list-providers

# ヘルプ表示
python auto_research.py --help
```

## ディレクトリ構造

```
auto-research/
├── auto_research.py              # メインスクリプト（Provider対応）
├── providers/                    # Provider実装
│   ├── __init__.py
│   ├── base.py                   # 抽象基底クラス
│   ├── perplexity_provider.py    # Perplexity API Provider
│   └── langchain_provider.py     # LangChain Provider (Phase 2-4)
├── config/
│   └── langchain.env             # LangChain専用設定
├── requirements.txt              # 依存関係
└── README.md                     # このファイル
```

## 設定管理

### 設定優先順位

1. コマンドライン引数 (`--config`)
2. Provider固有設定 (`config/langchain.env`)
3. デフォルト設定 (`.env`)

### LangChain Provider設定例

`config/langchain.env`:
```env
# Azure OpenAI settings
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_MODEL=gpt-4

# Search API settings (Phase 3)
TAVILY_API_KEY=your_tavily_key_here
SEARCH_MAX_RESULTS=10

# Multi-agent settings (Phase 4)
MAX_SUB_AGENTS=3
CONTEXT_COMPRESSION_THRESHOLD=4000
PARALLEL_EXECUTION_TIMEOUT=300
```

## 依存関係

### Phase 1 (現在)
```bash
pip install requests pathlib
```

### Phase 2-4 (将来)
```bash
# Phase 2
pip install openai azure-identity

# Phase 3
pip install tavily-python

# Phase 4
pip install langgraph langchain
```

## Provider詳細

### Perplexity Provider
- 既存システムの完全移植
- sonar-deep-research モデル使用
- 引用リンク自動生成
- 検索結果統合

### LangChain Provider (Phase 2-4で段階実装)
- **Phase 2**: Azure OpenAI基本統合
- **Phase 3**: Tavily Search API統合
- **Phase 4**: マルチエージェント協調

## 後方互換性

既存のスクリプトや設定は**完全に互換性が保たれています**：

- `python auto_research.py` は従来通り動作
- 既存の `.env` 設定ファイルをそのまま使用可能
- APIレスポンス形式は変更なし
- レポート出力形式は変更なし（Provider情報のみ追加）

## 開発者向け情報

### 新しいProvider追加方法

1. `providers/` ディレクトリに新しいProviderファイル作成
2. `ResearchProvider` 抽象クラスを継承
3. 必須メソッドを実装:
   - `conduct_research(prompt: str) -> Optional[Dict[str, Any]]`
   - `get_provider_name() -> str`
   - `validate_config() -> bool`
4. `providers/__init__.py` に追加
5. `ProviderFactory.create_provider()` に追加

### Architecture Pattern

システムはProvider パターン（Strategy パターン）を採用：

```python
# Factory Pattern
provider = ProviderFactory.create_provider(provider_type, config, logger)

# Strategy Pattern  
research_result = provider.conduct_research(prompt)
```

## トラブルシューティング

### LangChain Providerが利用できない場合

```bash
# 依存関係不足の場合
pip install openai azure-identity

# 設定不足の場合
cp config/langchain.env.example config/langchain.env
# config/langchain.env を編集
```

### デバッグモード

```bash
python auto_research.py --debug --provider langchain
```

詳細なログ出力で問題を特定できます。

## ライセンス

既存システムと同様のライセンス条項に従います。