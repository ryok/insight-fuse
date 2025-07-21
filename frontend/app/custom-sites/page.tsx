'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { format } from 'date-fns'
import {
  fetchCustomSites,
  deleteCustomSite,
  fetchAllCustomSites,
  initializeDefaultSites,
  CustomSite
} from '@/lib/api'
import CustomSiteForm from '@/components/CustomSiteForm'

export default function CustomSitesPage() {
  const [showForm, setShowForm] = useState(false)
  const [editingSite, setEditingSite] = useState<CustomSite | null>(null)
  const queryClient = useQueryClient()

  const { data: sites, isLoading } = useQuery({
    queryKey: ['customSites'],
    queryFn: () => fetchCustomSites(false), // 無効なサイトも含める
  })

  const deleteMutation = useMutation({
    mutationFn: deleteCustomSite,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customSites'] })
      alert('サイトを削除しました')
    },
    onError: () => {
      alert('削除に失敗しました')
    }
  })

  const fetchAllMutation = useMutation({
    mutationFn: fetchAllCustomSites,
    onSuccess: () => {
      alert('全サイトの取得を開始しました')
    },
    onError: () => {
      alert('取得開始に失敗しました')
    }
  })

  const initDefaultMutation = useMutation({
    mutationFn: initializeDefaultSites,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customSites'] })
      alert('デフォルトサイトを初期化しました')
    },
    onError: () => {
      alert('初期化に失敗しました')
    }
  })

  const handleEdit = (site: CustomSite) => {
    setEditingSite(site)
    setShowForm(true)
  }

  const handleAdd = () => {
    setEditingSite(null)
    setShowForm(true)
  }

  const handleFormClose = () => {
    setShowForm(false)
    setEditingSite(null)
  }

  const handleDelete = (site: CustomSite) => {
    if (confirm(`「${site.name}」を削除しますか？`)) {
      deleteMutation.mutate(site.id)
    }
  }

  const getSiteTypeLabel = (type: string) => {
    const types: Record<string, string> = {
      'substack': 'Substack',
      'newsletter': 'ニュースレター',
      'blog': 'ブログ',
      'generic': '汎用'
    }
    return types[type] || type
  }

  const getStatusBadge = (site: CustomSite) => {
    if (!site.enabled) {
      return <span className="text-xs bg-gray-500 text-white px-2 py-1 rounded">無効</span>
    }
    return <span className="text-xs bg-green-500 text-white px-2 py-1 rounded">有効</span>
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
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              カスタムサイト管理
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              定期取得するニュースサイトやブログを管理します
            </p>
          </div>
          
          <Link
            href="/"
            className="text-primary-500 hover:text-primary-600"
          >
            ← 記事一覧に戻る
          </Link>
        </div>

        {/* アクションボタン */}
        <div className="mb-6 flex flex-wrap gap-4">
          <button
            onClick={handleAdd}
            className="btn-primary"
          >
            新しいサイトを追加
          </button>
          
          <button
            onClick={() => fetchAllMutation.mutate()}
            disabled={fetchAllMutation.isPending}
            className="btn-secondary"
          >
            {fetchAllMutation.isPending ? '取得中...' : '全サイト取得実行'}
          </button>
          
          <button
            onClick={() => initDefaultMutation.mutate()}
            disabled={initDefaultMutation.isPending}
            className="btn-secondary"
          >
            {initDefaultMutation.isPending ? '初期化中...' : 'デフォルトサイト初期化'}
          </button>
        </div>

        {/* サイト一覧 */}
        {sites && sites.length > 0 ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {sites.map((site) => (
              <div key={site.id} className="card">
                <div className="space-y-3">
                  <div className="flex justify-between items-start">
                    <h3 className="text-lg font-semibold">{site.name}</h3>
                    {getStatusBadge(site)}
                  </div>
                  
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    <p><strong>URL:</strong> {site.url}</p>
                    <p><strong>タイプ:</strong> {getSiteTypeLabel(site.site_type)}</p>
                    <p><strong>言語:</strong> {site.language?.toUpperCase()}</p>
                    <p><strong>取得間隔:</strong> {site.fetch_interval_hours}時間</p>
                  </div>
                  
                  {site.category && (
                    <p className="text-sm">
                      <strong>カテゴリ:</strong> {site.category}
                    </p>
                  )}
                  
                  {site.tags && site.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {site.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-1 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                  
                  {site.last_fetched && (
                    <p className="text-xs text-gray-500">
                      最終取得: {format(new Date(site.last_fetched), 'yyyy/MM/dd HH:mm')}
                    </p>
                  )}
                  
                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={() => handleEdit(site)}
                      className="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
                    >
                      編集
                    </button>
                    
                    <Link
                      href={`/custom-sites/${site.id}/logs`}
                      className="text-sm bg-gray-500 text-white px-3 py-1 rounded hover:bg-gray-600"
                    >
                      ログ
                    </Link>
                    
                    <button
                      onClick={() => handleDelete(site)}
                      disabled={deleteMutation.isPending}
                      className="text-sm bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600 disabled:opacity-50"
                    >
                      削除
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              カスタムサイトが登録されていません
            </p>
            <button
              onClick={handleAdd}
              className="btn-primary"
            >
              最初のサイトを追加
            </button>
          </div>
        )}

        {/* サイト追加/編集フォーム */}
        {showForm && (
          <CustomSiteForm
            site={editingSite}
            onClose={handleFormClose}
            onSuccess={() => {
              queryClient.invalidateQueries({ queryKey: ['customSites'] })
              handleFormClose()
            }}
          />
        )}
      </div>
    </main>
  )
}