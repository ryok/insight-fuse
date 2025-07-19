# InsightFuse Backend

FastAPIベースのバックエンドサーバーです。

## 開発環境セットアップ

### uvのインストール

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 依存関係のインストール

```bash
# プロジェクト依存関係をインストール
uv sync

# 開発用依存関係も含める
uv sync --dev
```

### 環境変数の設定

```bash
cp .env.example .env
# .envファイルを編集してAPIキーなどを設定
```

### データベースのセットアップ

```bash
# PostgreSQLを起動（Docker Compose使用）
docker-compose up -d postgres

# データベースマイグレーション
uv run alembic upgrade head
```

### 開発サーバーの起動

```bash
uv run python run.py
```

## 開発コマンド

### テスト実行

```bash
# 全テスト実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov=app --cov-report=html
```

### コード品質チェック

```bash
# Linting
uv run ruff check .

# フォーマット
uv run black .

# 型チェック
uv run mypy .
```

### 自動フォーマット＆修正

```bash
# Ruffで自動修正可能な問題を修正
uv run ruff check . --fix

# Blackでコードフォーマット
uv run black .
```

## プロジェクト構造

```
app/
├── api/           # API エンドポイント
├── core/          # アプリケーション設定
├── db/            # データベース関連
├── schemas/       # Pydantic スキーマ
└── services/      # ビジネスロジック
```

## 新しい依存関係の追加

```bash
# 本番依存関係を追加
uv add package-name

# 開発用依存関係を追加
uv add --dev package-name

# 特定のバージョンを指定
uv add "package-name>=1.0.0"
```

## API ドキュメント

サーバー起動後、以下のURLでAPIドキュメントを確認できます：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc