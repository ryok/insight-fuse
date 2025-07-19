# InsightFuse - AI-Powered News Aggregation & Analysis Platform

InsightFuseは、技術ニュースを自動収集し、AI（LLM）を活用して要約・分析を行うWebアプリケーションです。英語、日本語、中国語の多言語対応で、TOEIC 800点レベルの語彙解説や今後の影響分析など、理解を深める機能を提供します。

## 主な機能

- **多言語ニュース収集**: 英語、日本語、中国語のニュースソースから自動収集
- **AI要約**: 記事の要点を多言語で自動要約
- **語彙分析**: TOEIC 800点以上レベルの英単語を日本語で解説
- **背景・影響分析**: ニュースの背景説明と今後の影響を分析
- **SNS投稿支援**: ブログやSNS用のタイトル案を自動生成

## 技術スタック

### バックエンド
- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL
- OpenAI API / Anthropic Claude API

### フロントエンド
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- TanStack Query (React Query)

## セットアップ

### 前提条件
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- uv (Python package manager)
- PostgreSQL (Dockerで提供)

### 環境変数の設定

1. バックエンドの環境変数をコピー:
```bash
cp backend/.env.example backend/.env
```

2. `.env`ファイルを編集して、必要なAPIキーを設定:
```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional
NEWS_API_KEY=your_newsapi_key
```

### Docker Composeで起動

```bash
# データベースとバックエンドを起動
docker-compose up -d

# フロントエンドの依存関係をインストール
cd frontend
npm install

# フロントエンドを起動
npm run dev
```

### 手動セットアップ（開発用）

1. **データベースの起動**:
```bash
docker-compose up -d postgres
```

2. **バックエンドのセットアップ**:

まず、uvをインストール（未インストールの場合）:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

バックエンドの起動:
```bash
cd backend

# 依存関係のインストール
uv sync

# データベースマイグレーション
uv run alembic upgrade head

# 開発サーバー起動
uv run python run.py
```

3. **フロントエンドのセットアップ**:
```bash
cd frontend
npm install
npm run dev
```

## 使い方

1. ブラウザで `http://localhost:3000` にアクセス
2. 「Fetch News」ボタンをクリックして最新ニュースを取得
3. 記事をクリックして詳細ページへ
4. 要約生成や分析機能を利用

## API エンドポイント

- `GET /api/v1/articles` - 記事一覧を取得
- `GET /api/v1/articles/{id}` - 記事詳細を取得
- `POST /api/v1/summaries/article/{id}` - 要約を生成
- `POST /api/v1/analyses/article/{id}` - 分析を生成
- `POST /api/v1/fetch/news` - ニュース取得を開始

## 開発

### テストの実行
```bash
# バックエンド
cd backend
uv run pytest

# フロントエンド
cd frontend
npm test
```

### リンターとフォーマッターの実行
```bash
# バックエンド
cd backend
uv run ruff check .    # Linting
uv run black .         # Formatting
uv run mypy .          # Type checking

# フロントエンド
cd frontend
npm run lint
```

## ライセンス

ISC License

## 貢献

プルリクエストは歓迎します。大きな変更の場合は、まずissueを作成して変更内容を議論してください。
