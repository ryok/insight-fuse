# Gmail API セットアップガイド

InsightFuseでGmailから特定のメールレターを自動取得するためのセットアップ手順です。

## 1. Google Cloud Console での設定

### 1.1 プロジェクト作成
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成、または既存のプロジェクトを選択
3. プロジェクト名を「InsightFuse」などに設定

### 1.2 Gmail API の有効化
1. サイドメニューから「APIとサービス」→「ライブラリ」をクリック
2. 「Gmail API」を検索して選択
3. 「有効にする」をクリック

### 1.3 認証情報の作成
1. サイドメニューから「APIとサービス」→「認証情報」をクリック
2. 「認証情報を作成」→「OAuthクライアントID」を選択
3. アプリケーションの種類で「デスクトップアプリケーション」を選択
4. 名前を「InsightFuse Gmail Client」などに設定
5. 作成をクリック

### 1.4 認証情報ファイルのダウンロード
1. 作成されたOAuthクライアントIDの右側にある「ダウンロード」アイコンをクリック
2. JSONファイルをダウンロード
3. ファイル名を `credentials.json` に変更

## 2. 認証情報ファイルの配置

### ローカル開発環境
```bash
# バックエンドディレクトリに credentials.json を配置
cp path/to/your/credentials.json backend/credentials.json
```

### Docker環境
```bash
# Dockerコンテナに認証情報をマウント
# docker-compose.yml に以下を追加:

services:
  backend:
    volumes:
      - ./backend/credentials.json:/app/credentials.json:ro
```

## 3. 初回認証の実行

アプリケーションを起動し、Gmail設定ページで「Gmail接続テスト」を実行すると、初回認証プロセスが開始されます。

1. ブラウザが自動で開きます
2. Googleアカウントでログイン
3. アプリケーションのアクセス許可を承認
4. 認証完了後、`token.json` ファイルが自動生成されます

## 4. メールレター設定の作成

### 4.1 基本的な設定例

**AI Weekly Newsletter の場合:**
```
設定名: AI Weekly Newsletter
送信者メールアドレス: newsletter@aiweekly.com
件名キーワード: AI, Weekly, machine learning
カテゴリ: ai
言語: en
取得間隔: 24時間
```

**日本語ニュースレターの場合:**
```
設定名: 週刊技術ニュース
送信者メールアドレス: news@techblog.jp
件名キーワード: 週刊, 技術, ニュース
除外キーワード: 配信停止, unsubscribe
カテゴリ: technology
言語: ja
```

### 4.2 フィルタリング設定のコツ

**送信者フィルター:**
- `sender_email`: 特定の送信者からのメールのみ取得
- `sender_name`: 送信者名での絞り込み

**件名フィルター:**
- `subject_keywords`: いずれかのキーワードを含む
- `exclude_keywords`: これらのキーワードを含むメールは除外

**Gmail検索クエリの例:**
```
from:newsletter@example.com subject:(AI OR "machine learning") -unsubscribe
```

## 5. 自動取得の仕組み

### 5.1 取得プロセス
1. 設定された間隔でGmail APIにアクセス
2. フィルター条件に基づいてメールを検索
3. 新しいメールの内容を抽出・解析
4. 記事形式でデータベースに保存
5. 重複チェックで同じメールの再保存を防止

### 5.2 コンテンツ処理
- **HTMLメール**: BeautifulSoupでパース、テキスト抽出
- **プレーンテキスト**: そのまま使用
- **言語検出**: 自動で言語を検出
- **カテゴリ分類**: 内容に基づいてカテゴリを推定

## 6. トラブルシューティング

### 6.1 よくあるエラー

**認証エラー:**
```
Error: Please place your Google API credentials in credentials.json
```
→ `credentials.json` ファイルが正しく配置されているか確認

**API制限エラー:**
```
Error: Quota exceeded
```
→ Gmail APIの利用制限に達した場合は、時間をおいて再実行

**権限エラー:**
```
Error: Insufficient permissions
```
→ OAuth認証で必要な権限が付与されているか確認

### 6.2 デバッグ方法

1. **接続テスト**: Gmail設定ページの「接続テスト」ボタンで基本的な接続を確認
2. **ログ確認**: バックエンドのログでエラー詳細を確認
3. **手動取得**: 特定の設定で「取得」ボタンを押して動作確認

## 7. セキュリティとプライバシー

### 7.1 権限スコープ
- 使用権限: `https://www.googleapis.com/auth/gmail.readonly` (読み取り専用)
- メールの削除・送信は行いません

### 7.2 データ保護
- 認証トークンは暗号化して保存
- メール内容は必要な情報のみ抽出
- 個人情報の処理に注意

## 8. 運用のベストプラクティス

### 8.1 効率的な設定
- **絞り込み**: 不要なメールを除外するフィルターを設定
- **間隔調整**: ニュースレターの頻度に合わせて取得間隔を設定
- **制限設定**: `max_emails_per_fetch` で一度に処理する量を制限

### 8.2 監視とメンテナンス
- 定期的に取得ログを確認
- エラー率の高い設定は見直し
- 不要になった設定は無効化または削除

## 9. 応用例

### 9.1 複数ニュースレターの一括管理
```
AI関連: OpenAI, Anthropic, Google AI のニュースレター
技術系: GitHub, Stack Overflow, Developer Weekly
ビジネス系: TechCrunch, VentureBeat の週次まとめ
```

### 9.2 言語別設定
```
英語: 海外の技術ニュースレター
日本語: 国内の技術ブログ、企業ニュースレター
中国語: 中国系テック企業の情報
```

この設定により、Gmailから自動的にメールレターを取得し、InsightFuseの記事として管理できます。