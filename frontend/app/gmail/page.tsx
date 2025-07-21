'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { format } from 'date-fns'
import GmailNewsletterForm, { GmailNewsletter } from '@/components/GmailNewsletterForm'

// API関数
async function fetchGmailNewsletters(enabledOnly: boolean = true) {
  const response = await fetch(`/api/v1/gmail/newsletters?enabled_only=${enabledOnly}`)
  if (!response.ok) {
    throw new Error('Failed to fetch Gmail newsletters')
  }
  return response.json()
}

async function deleteGmailNewsletter(id: number) {
  const response = await fetch(`/api/v1/gmail/newsletters/${id}`, {
    method: 'DELETE'
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to delete newsletter')
  }
  return response.json()
}

async function fetchGmailNewsletter(id: number) {
  const response = await fetch(`/api/v1/gmail/newsletters/${id}/fetch`, {
    method: 'POST'
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch emails')
  }
  return response.json()
}

async function fetchAllGmailNewsletters() {
  const response = await fetch('/api/v1/gmail/fetch-all', {
    method: 'POST'
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch all emails')
  }
  return response.json()
}

async function testGmailConnection() {
  const response = await fetch('/api/v1/gmail/test-connection', {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error('Failed to test Gmail connection')
  }
  return response.json()
}

export default function GmailPage() {
  const [showForm, setShowForm] = useState(false)
  const [editingNewsletter, setEditingNewsletter] = useState<GmailNewsletter | null>(null)
  const [showAll, setShowAll] = useState(false)
  
  const queryClient = useQueryClient()

  const { data: newsletters, isLoading, error } = useQuery({
    queryKey: ['gmail-newsletters', showAll],
    queryFn: () => fetchGmailNewsletters(!showAll),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteGmailNewsletter,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gmail-newsletters'] })
      alert('ニュースレター設定を削除しました')
    },
    onError: (error: any) => {
      alert(`削除エラー: ${error.message}`)
    }
  })

  const fetchMutation = useMutation({
    mutationFn: fetchGmailNewsletter,
    onSuccess: () => {
      alert('メール取得を開始しました')
    },
    onError: (error: any) => {
      alert(`取得エラー: ${error.message}`)
    }
  })

  const fetchAllMutation = useMutation({
    mutationFn: fetchAllGmailNewsletters,
    onSuccess: () => {
      alert('全てのニュースレターのメール取得を開始しました')
    },
    onError: (error: any) => {
      alert(`取得エラー: ${error.message}`)
    }
  })

  const testConnectionMutation = useMutation({
    mutationFn: testGmailConnection,
    onSuccess: (data) => {
      alert(`接続テスト成功: ${data.message}`)
    },
    onError: (error: any) => {
      alert(`接続テストエラー: ${error.message}`)
    }
  })

  const handleEdit = (newsletter: GmailNewsletter) => {
    setEditingNewsletter(newsletter)
    setShowForm(true)
  }

  const handleDelete = (newsletter: GmailNewsletter) => {
    if (confirm(`「${newsletter.name}」を削除しますか？`)) {
      deleteMutation.mutate(newsletter.id)
    }
  }

  const handleCloseForm = () => {
    setShowForm(false)
    setEditingNewsletter(null)
  }

  const handleFormSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['gmail-newsletters'] })
    handleCloseForm()
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Gmail ニュースレター設定</h1>
            <p className="text-gray-600 dark:text-gray-400">
              Gmailから特定のメールレターを自動取得する設定を管理します
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/" className="btn-secondary">
              ← 戻る
            </Link>
            <button
              onClick={() => testConnectionMutation.mutate()}
              disabled={testConnectionMutation.isPending}
              className="btn-secondary"
            >
              {testConnectionMutation.isPending ? 'テスト中...' : 'Gmail接続テスト'}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            エラー: {error.message}
          </div>
        )}

        {/* 操作パネル */}
        <div className="card mb-6">
          <div className="flex flex-wrap gap-4 items-center justify-between">
            <div className="flex gap-2">
              <button
                onClick={() => setShowForm(true)}
                className="btn-primary"
              >
                + 新しい設定を追加
              </button>
              
              <button
                onClick={() => fetchAllMutation.mutate()}
                disabled={fetchAllMutation.isPending}
                className="btn-secondary"
              >
                {fetchAllMutation.isPending ? '取得中...' : '全て取得'}
              </button>
            </div>

            <div className="flex items-center gap-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={showAll}
                  onChange={(e) => setShowAll(e.target.checked)}
                  className="mr-2"
                />
                無効な設定も表示
              </label>
            </div>
          </div>
        </div>

        {/* ニュースレター一覧 */}
        {newsletters && newsletters.length > 0 ? (
          <div className="space-y-4">
            {newsletters.map((newsletter: GmailNewsletter) => (
              <div key={newsletter.id} className="card">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold">{newsletter.name}</h3>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        newsletter.enabled 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      }`}>
                        {newsletter.enabled ? '有効' : '無効'}
                      </span>
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded-full">
                        {newsletter.category}
                      </span>
                      <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200 rounded-full">
                        {newsletter.language}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 dark:text-gray-400">
                      {newsletter.sender_email && (
                        <div>
                          <span className="font-medium">送信者:</span> {newsletter.sender_email}
                        </div>
                      )}
                      
                      <div>
                        <span className="font-medium">取得間隔:</span> {newsletter.fetch_interval_hours}時間
                      </div>
                      
                      <div>
                        <span className="font-medium">最大取得数:</span> {newsletter.max_emails_per_fetch}件
                      </div>
                      
                      <div>
                        <span className="font-medium">処理済み:</span> {newsletter.total_emails_processed}件
                      </div>
                    </div>

                    {newsletter.subject_keywords && newsletter.subject_keywords.length > 0 && (
                      <div className="mt-2">
                        <span className="text-sm font-medium">件名キーワード: </span>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {newsletter.subject_keywords.join(', ')}
                        </span>
                      </div>
                    )}

                    {newsletter.tags && newsletter.tags.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {newsletter.tags.map((tag, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {newsletter.last_fetched && (
                      <div className="mt-2 text-sm text-gray-500">
                        最終取得: {format(new Date(newsletter.last_fetched), 'yyyy/MM/dd HH:mm')}
                      </div>
                    )}
                  </div>

                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => fetchMutation.mutate(newsletter.id)}
                      disabled={fetchMutation.isPending || !newsletter.enabled}
                      className="btn-secondary text-sm"
                    >
                      取得
                    </button>
                    
                    <button
                      onClick={() => handleEdit(newsletter)}
                      className="btn-secondary text-sm"
                    >
                      編集
                    </button>
                    
                    <button
                      onClick={() => handleDelete(newsletter)}
                      disabled={deleteMutation.isPending}
                      className="text-red-600 hover:text-red-800 text-sm px-2"
                    >
                      削除
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card text-center py-12">
            <div className="text-gray-500 dark:text-gray-400 mb-4">
              <svg className="mx-auto h-16 w-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <p className="text-lg">Gmail ニュースレター設定がありません</p>
              <p className="text-sm mt-2">「新しい設定を追加」ボタンから最初の設定を作成してください</p>
            </div>
            <button
              onClick={() => setShowForm(true)}
              className="btn-primary"
            >
              設定を作成
            </button>
          </div>
        )}

        {/* Gmail設定の説明 */}
        <div className="card mt-8 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <h3 className="text-lg font-semibold mb-3 text-blue-900 dark:text-blue-200">
            Gmail API設定について
          </h3>
          <div className="text-sm text-blue-800 dark:text-blue-300 space-y-2">
            <p>• Gmail APIを使用するには、Google Cloud Consoleでプロジェクトを作成し、Gmail APIを有効化する必要があります</p>
            <p>• 認証情報（credentials.json）をバックエンドに配置してください</p>
            <p>• 初回実行時にブラウザで認証が必要です</p>
            <p>• 設定したフィルターに基づいて自動的にメールが取得され、記事として保存されます</p>
          </div>
        </div>
      </div>

      {/* フォームモーダル */}
      {showForm && (
        <GmailNewsletterForm
          newsletter={editingNewsletter}
          onClose={handleCloseForm}
          onSuccess={handleFormSuccess}
        />
      )}
    </main>
  )
}