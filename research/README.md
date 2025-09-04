# 自動リサーチシステム - Provider パターン版

Provider パターンによる拡張可能な自動リサーチシステム。Obsidian日記から注目ワードを抽出し、選択されたProviderでリサーチを実行して結果を保存します。

## 🎯 特徴

### Phase 1: Provider パターン基盤 ✅
- **拡張可能アーキテクチャ**: Provider パターン + Factory パターン
- **100% 後方互換性**: 既存スクリプトが変更なしで動作
- **コマンドライン インターフェース**: プロバイダー選択、設定管理、デバッグモード

### Phase 2: Azure OpenAI統合 ✅ 
- **Azure OpenAI基本統合**: GPT-4による高品質リサーチ
- **エラーハンドリング**: リトライ機構とコスト制御
- **設定管理**: 階層的設定システム

### Phase 3: 検索API統合 ✅
- **Tavily Search API統合**: リアルタイム情報取得
- **引用管理**: 自動リンク生成と参考文献リスト
- **フィルタリング**: 重複排除とレート制限対応

### Phase 4: マルチエージェント協調 ✅
- **研究スーパーバイザー**: クエリ分解とサブタスク生成
- **並列専門エージェント**: 複数専門分野の同時リサーチ
- **コンテキスト圧縮**: トークン最適化と統合分析
- **品質評価**: 信頼度スコアリングとエビデンス統合

## 🚀 使用方法

### 基本コマンド

```bash
# デフォルト (Perplexity API - 既存動作)
python auto_research.py

# プロバイダー明示指定
python auto_research.py --provider perplexity
python auto_research.py --provider langchain

# 高度なオプション
python auto_research.py -p langchain --config custom.env --debug
python auto_research.py --list-providers
```

### プロバイダー比較

| プロバイダー | 特徴 | 適用フェーズ | エージェント数 |
|-------------|------|-------------|---------------|
| **perplexity** | Perplexity API、単一エージェント | Phase 1 | 1 |
| **langchain** | Azure OpenAI + 検索 + マルチエージェント | Phase 2-4 | 1-3 |

## ⚙️ 設定

### 階層的設定システム

設定の優先順位: `CLI引数` > `カスタム.env` > `プロバイダー.env` > `.env` > `デフォルト値`

### Perplexity Provider設定 (.env)

```env
PERPLEXITY_API_KEY=your_perplexity_api_key_here
USER_INFO_PATH=/path/to/obsidian/diary
PROMPT_TEMPLATE_PATH=/path/to/prompt_template.md
RESEARCH_REPORT_PATH=/path/to/output/reports
```

### LangChain Provider設定 (config/langchain.env)

```env
# Phase 2: Azure OpenAI Settings
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/v1/
AZURE_OPENAI_MODEL=gpt-4

# Phase 3: Search API Settings
TAVILY_API_KEY=your_tavily_api_key
SEARCH_MAX_RESULTS=10

# Phase 4: Multi-agent Settings
MAX_SUB_AGENTS=3
CONTEXT_COMPRESSION_THRESHOLD=4000
PARALLEL_EXECUTION_TIMEOUT=300
```

## 🏗️ システムアーキテクチャ

### Provider パターン基盤

```
[CLI] → [AutoResearchSystem] → [ProviderFactory]
                                      ↓
                              [PerplexityProvider]
                              [LangChainProvider]
```

### マルチエージェント協調システム (Phase 4)

```
[入力統合層] → [研究戦略層] → [多角実行層] → [統合分析層] → [出力生成層]
     ↓            ↓           ↓           ↓          ↓
[日記読込み] → [クエリ分解] → [並列エージェント] → [統合分析] → [レポート生成]
```

## 📁 プロジェクト構造

```
auto-research/
├── auto_research.py              # メインシステム
├── providers/
│   ├── __init__.py
│   ├── base.py                   # 抽象基底クラス
│   ├── perplexity_provider.py    # Perplexity API provider
│   ├── langchain_provider.py     # LangChain multi-agent provider
│   └── factory.py                # Provider factory
├── config/
│   └── langchain.env             # LangChain設定テンプレート
├── requirements.txt              # 依存関係
└── README.md                     # 本ファイル
```

## 🔧 セットアップ

### 1. 依存関係インストール

```bash
pip install -r requirements.txt
```

### 2. 設定ファイル準備

```bash
# Perplexity用 (既存)
cp .env.example .env
# LangChain用 (新規)
cp config/langchain.env config/custom.env
```

### 3. API キー設定

各プロバイダーに必要なAPIキーを設定ファイルに記述します。

## 📊 出力フォーマット

生成されるレポートには以下が含まれます:

### メタデータセクション

```markdown
## 生成メタデータ

- **プロバイダー**: langchain
- **エージェント数**: 3
- **信頼度スコア**: 0.87
```

### 参考文献 (自動リンク生成)

```markdown
## 参考文献

1. [OpenAI GPT-4 Technical Report](https://openai.com/research/gpt-4)
2. [LangChain Documentation](https://python.langchain.com/)
```

## 🎛️ 高度な機能

### デバッグモード

```bash
python auto_research.py --debug --provider langchain
```

- 詳細ログ出力
- プロンプト内容表示
- エラートレースバック

### カスタム設定

```bash
python auto_research.py --config production.env --provider langchain
```

## 🔍 技術実装詳細

### Phase 2: Azure OpenAI統合

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    base_url="https://your-resource.openai.azure.com/openai/v1/"
)
```

### Phase 3: 検索API統合

```python
from tavily import TavilyClient

search_client = TavilyClient(api_key=api_key)
results = search_client.search(query="...", search_depth="deep")
```

### Phase 4: マルチエージェント協調

```python
# 並列専門エージェント実行
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(agent.research, query) for agent in agents]
    results = [f.result() for f in futures]
```

## 📚 実装リファレンス

### 設計パターン

- **Abstract Factory Pattern**: プロバイダー作成
- **Strategy Pattern**: アルゴリズム切り替え  
- **Template Method**: 共通処理フロー

### 外部ライブラリ

- **OpenAI Python SDK**: Azure OpenAI統合
- **Tavily Python**: リアルタイム検索
- **LangChain**: エージェント協調 (オプション)

## 🚨 注意事項

### API使用コスト

- **Perplexity**: リクエスト毎課金
- **Azure OpenAI**: トークン毎課金
- **Tavily**: 検索クエリ毎課金

### 並列実行制限

- デフォルトエージェント数: 3
- タイムアウト: 300秒
- コンテキスト圧縮閾値: 4000文字

## 🔮 将来の拡張

### 追加Provider候補

- **Claude Provider**: Anthropic Claude API
- **Local Provider**: ローカルLLM (Ollama等)
- **Custom Provider**: 企業内API

### 機能拡張

- **エージェント特化**: 分野別専門エージェント
- **知識ベース**: 継続学習と知識蓄積
- **ワークフロー**: 複雑なマルチステップタスク
