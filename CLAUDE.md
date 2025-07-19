# InsightFuse - 毎日の情報収集支援・自動化アプリ

## プロジェクト概要
InsightFuseは、技術情報、ニュース、論文情報を毎日自動で収集し、LLMを活用して理解とアイディア創出を支援するアプリケーションです。

## 主要機能

### 1. 情報収集機能
- 英語、中国語、日本語のニュースソースから最新情報を取得
- AI・技術関連のニュースに特化
- 論文情報の収集

### 2. LLMによる分析・要約機能
- ニュース内容の要約（英語・日本語）
- TOEIC 800点以上レベルの英単語の日本語解説
- ニュースの背景・文脈の説明
- 今後の影響に関する考察（500文字程度）
- ブログ・SNS投稿用のタイトル案生成

## 技術スタック（推奨）
- **バックエンド**: Python (FastAPI) または Node.js (Express)
- **フロントエンド**: React/Next.js または Vue.js
- **データベース**: PostgreSQL または MongoDB
- **LLM API**: OpenAI API または Claude API
- **ニュースAPI**: NewsAPI, Google News API, RSS feeds
- **スケジューラー**: Cron job または GitHub Actions

## 実装方針

### Phase 1: 基本機能の実装
1. ニュースAPI連携の実装
2. 基本的なデータ保存機能
3. シンプルなWeb UI

### Phase 2: LLM統合
1. LLM APIの統合
2. 要約・分析機能の実装
3. 多言語対応

### Phase 3: 自動化・拡張
1. 定期実行の設定
2. 通知機能（メール、Slack等）
3. カスタマイズ可能なフィルター

## 開発環境セットアップ
```bash
# プロジェクトの初期化
npm init -y  # または yarn init -y

# 必要な依存関係のインストール
# (具体的なコマンドは選択した技術スタックに依存)
```

## テストコマンド
```bash
# テストの実行
npm test

# リントチェック
npm run lint

# 型チェック（TypeScriptの場合）
npm run typecheck
```

## 注意事項
- APIキーは環境変数で管理すること
- レート制限に注意（特にニュースAPIとLLM API）
- 著作権とライセンスに配慮した情報の取り扱い