'use client'

import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { 
  createCustomSite,
  updateCustomSite,
  analyzeSiteUrl,
  CustomSite,
  CustomSiteCreate,
  CustomSiteUpdate
} from '@/lib/api'

interface CustomSiteFormProps {
  site?: CustomSite | null
  onClose: () => void
  onSuccess: () => void
}

const siteTypes = [
  { value: 'substack', label: 'Substack' },
  { value: 'newsletter', label: 'ニュースレター' },
  { value: 'blog', label: 'ブログ' },
  { value: 'generic', label: '汎用サイト' }
]

const languages = [
  { value: 'en', label: 'English' },
  { value: 'ja', label: '日本語' },
  { value: 'zh', label: '中文' }
]

const categories = [
  { value: 'technology', label: 'テクノロジー' },
  { value: 'ai', label: 'AI・機械学習' },
  { value: 'data-science', label: 'データサイエンス' },
  { value: 'startup', label: 'スタートアップ' },
  { value: 'business', label: 'ビジネス' },
  { value: 'science', label: '科学' },
  { value: 'creative-ai', label: 'クリエイティブAI' },
  { value: 'newsletter', label: 'ニュースレター' },
  { value: 'other', label: 'その他' }
]

export default function CustomSiteForm({ site, onClose, onSuccess }: CustomSiteFormProps) {
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    site_type: 'newsletter',
    language: 'en',
    category: 'technology',
    tags: '',
    enabled: true,
    fetch_interval_hours: 24
  })

  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const isEditing = !!site

  useEffect(() => {
    if (site) {
      setFormData({
        name: site.name,
        url: site.url,
        site_type: site.site_type,
        language: site.language || 'en',
        category: site.category || 'technology',
        tags: site.tags?.join(', ') || '',
        enabled: site.enabled,
        fetch_interval_hours: site.fetch_interval_hours
      })
    }
  }, [site])

  const createMutation = useMutation({
    mutationFn: createCustomSite,
    onSuccess: () => {
      alert('サイトを追加しました')
      onSuccess()
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || '追加に失敗しました'
      alert(`エラー: ${errorMessage}`)
      console.error('Create error:', error)
    }
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number, data: CustomSiteUpdate }) => 
      updateCustomSite(id, data),
    onSuccess: () => {
      alert('サイトを更新しました')
      onSuccess()
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || '更新に失敗しました'
      alert(`エラー: ${errorMessage}`)
      console.error('Update error:', error)
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const tags = formData.tags
      .split(',')
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0)

    const submitData = {
      ...formData,
      tags: tags.length > 0 ? tags : undefined
    }

    if (isEditing && site) {
      updateMutation.mutate({ id: site.id, data: submitData })
    } else {
      createMutation.mutate(submitData as CustomSiteCreate)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : 
               type === 'number' ? parseInt(value) || 0 : value
    }))
  }

  const handleUrlBlur = async () => {
    if (!formData.url || isEditing || isAnalyzing) return
    
    // URLの形式をチェック
    try {
      new URL(formData.url)
    } catch {
      return // 不正なURLの場合は何もしない
    }

    setIsAnalyzing(true)
    
    try {
      const result = await analyzeSiteUrl(formData.url)
      
      if (result.success && result.data) {
        const siteInfo = result.data
        
        // フォームデータを自動更新（空の項目のみ）
        setFormData(prev => ({
          ...prev,
          name: prev.name || siteInfo.name || '',
          site_type: siteInfo.site_type || prev.site_type,
          language: siteInfo.language || prev.language,
          category: siteInfo.category || prev.category,
          tags: prev.tags || (siteInfo.tags ? siteInfo.tags.join(', ') : '')
        }))
        
        // 成功メッセージを表示（簡単な通知）
        console.log('Site info auto-filled:', siteInfo)
      }
    } catch (error) {
      console.error('Failed to analyze URL:', error)
      // エラーは無視して、ユーザーが手動で入力できるようにする
    } finally {
      setIsAnalyzing(false)
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">
              {isEditing ? 'サイト編集' : '新しいサイトを追加'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* サイト名 */}
            <div>
              <label className="block text-sm font-medium mb-1">
                サイト名 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="例: Weekly Kaggle News"
              />
            </div>

            {/* URL */}
            <div>
              <label className="block text-sm font-medium mb-1">
                URL <span className="text-red-500">*</span>
                {isAnalyzing && (
                  <span className="ml-2 text-primary-500 text-xs">
                    📡 サイト情報を取得中...
                  </span>
                )}
              </label>
              <input
                type="url"
                name="url"
                value={formData.url}
                onChange={handleChange}
                onBlur={handleUrlBlur}
                required
                disabled={isAnalyzing}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
                placeholder="https://example.com"
              />
              {!isEditing && (
                <p className="text-xs text-gray-500 mt-1">
                  URLを入力すると、サイト名や言語などの情報を自動で取得します
                </p>
              )}
            </div>

            {/* サイトタイプ */}
            <div>
              <label className="block text-sm font-medium mb-1">
                サイトタイプ <span className="text-red-500">*</span>
              </label>
              <select
                name="site_type"
                value={formData.site_type}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {siteTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* 言語 */}
              <div>
                <label className="block text-sm font-medium mb-1">言語</label>
                <select
                  name="language"
                  value={formData.language}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  {languages.map(lang => (
                    <option key={lang.value} value={lang.value}>
                      {lang.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* カテゴリ */}
              <div>
                <label className="block text-sm font-medium mb-1">カテゴリ</label>
                <select
                  name="category"
                  value={formData.category}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  {categories.map(cat => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* タグ */}
            <div>
              <label className="block text-sm font-medium mb-1">
                タグ
                <span className="text-sm text-gray-500 ml-2">（カンマ区切り）</span>
              </label>
              <input
                type="text"
                name="tags"
                value={formData.tags}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="例: kaggle, machine-learning, competitions"
              />
            </div>

            {/* 取得間隔 */}
            <div>
              <label className="block text-sm font-medium mb-1">
                取得間隔（時間）
              </label>
              <input
                type="number"
                name="fetch_interval_hours"
                value={formData.fetch_interval_hours}
                onChange={handleChange}
                min="1"
                max="168"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="text-sm text-gray-500 mt-1">
                1〜168時間（1週間）の間で設定してください
              </p>
            </div>

            {/* 有効/無効 */}
            <div className="flex items-center">
              <input
                type="checkbox"
                name="enabled"
                id="enabled"
                checked={formData.enabled}
                onChange={handleChange}
                className="mr-2"
              />
              <label htmlFor="enabled" className="text-sm font-medium">
                サイトを有効にする
              </label>
            </div>

            {/* ボタン */}
            <div className="flex gap-4 pt-6">
              <button
                type="submit"
                disabled={isPending}
                className="btn-primary flex-1 disabled:opacity-50"
              >
                {isPending ? '保存中...' : (isEditing ? '更新' : '追加')}
              </button>
              
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary flex-1"
              >
                キャンセル
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}