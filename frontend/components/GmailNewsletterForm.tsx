'use client'

import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'

export interface GmailNewsletter {
  id: number
  name: string
  sender_email?: string
  sender_name?: string
  subject_keywords?: string[]
  exclude_keywords?: string[]
  category: string
  tags?: string[]
  language: string
  enabled: boolean
  fetch_interval_hours: number
  max_emails_per_fetch: number
  days_back: number
  last_fetched?: string
  total_emails_processed: number
  created_at: string
  updated_at: string
}

export interface GmailNewsletterCreate {
  name: string
  sender_email?: string
  sender_name?: string
  subject_keywords?: string[]
  exclude_keywords?: string[]
  category: string
  tags?: string[]
  language: string
  enabled: boolean
  fetch_interval_hours: number
  max_emails_per_fetch: number
  days_back: number
}

export interface GmailNewsletterUpdate {
  name?: string
  sender_email?: string
  sender_name?: string
  subject_keywords?: string[]
  exclude_keywords?: string[]
  category?: string
  tags?: string[]
  language?: string
  enabled?: boolean
  fetch_interval_hours?: number
  max_emails_per_fetch?: number
  days_back?: number
}

interface GmailNewsletterFormProps {
  newsletter?: GmailNewsletter | null
  onClose: () => void
  onSuccess: () => void
}

const categories = [
  { value: 'newsletter', label: 'ニュースレター' },
  { value: 'ai', label: 'AI・機械学習' },
  { value: 'tech', label: 'テクノロジー' },
  { value: 'data', label: 'データサイエンス' },
  { value: 'business', label: 'ビジネス' },
  { value: 'science', label: '科学' },
  { value: 'startup', label: 'スタートアップ' },
  { value: 'other', label: 'その他' }
]

const languages = [
  { value: 'en', label: 'English' },
  { value: 'ja', label: '日本語' },
  { value: 'zh', label: '中文' }
]

// API関数
async function createGmailNewsletter(data: GmailNewsletterCreate) {
  const response = await fetch('/api/v1/gmail/newsletters', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to create newsletter')
  }
  return response.json()
}

async function updateGmailNewsletter(id: number, data: GmailNewsletterUpdate) {
  const response = await fetch(`/api/v1/gmail/newsletters/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to update newsletter')
  }
  return response.json()
}

export default function GmailNewsletterForm({ newsletter, onClose, onSuccess }: GmailNewsletterFormProps) {
  const [formData, setFormData] = useState({
    name: '',
    sender_email: '',
    sender_name: '',
    subject_keywords: '',
    exclude_keywords: '',
    category: 'newsletter',
    tags: '',
    language: 'en',
    enabled: true,
    fetch_interval_hours: 24,
    max_emails_per_fetch: 10,
    days_back: 7
  })

  const isEditing = !!newsletter

  useEffect(() => {
    if (newsletter) {
      setFormData({
        name: newsletter.name,
        sender_email: newsletter.sender_email || '',
        sender_name: newsletter.sender_name || '',
        subject_keywords: newsletter.subject_keywords?.join(', ') || '',
        exclude_keywords: newsletter.exclude_keywords?.join(', ') || '',
        category: newsletter.category,
        tags: newsletter.tags?.join(', ') || '',
        language: newsletter.language,
        enabled: newsletter.enabled,
        fetch_interval_hours: newsletter.fetch_interval_hours,
        max_emails_per_fetch: newsletter.max_emails_per_fetch,
        days_back: newsletter.days_back
      })
    }
  }, [newsletter])

  const createMutation = useMutation({
    mutationFn: createGmailNewsletter,
    onSuccess: () => {
      alert('Gmailニュースレター設定を作成しました')
      onSuccess()
    },
    onError: (error: any) => {
      const errorMessage = error.message || '作成に失敗しました'
      alert(`エラー: ${errorMessage}`)
      console.error('Create error:', error)
    }
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number, data: GmailNewsletterUpdate }) => 
      updateGmailNewsletter(id, data),
    onSuccess: () => {
      alert('Gmailニュースレター設定を更新しました')
      onSuccess()
    },
    onError: (error: any) => {
      const errorMessage = error.message || '更新に失敗しました'
      alert(`エラー: ${errorMessage}`)
      console.error('Update error:', error)
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const subject_keywords = formData.subject_keywords
      .split(',')
      .map(keyword => keyword.trim())
      .filter(keyword => keyword.length > 0)

    const exclude_keywords = formData.exclude_keywords
      .split(',')
      .map(keyword => keyword.trim())
      .filter(keyword => keyword.length > 0)

    const tags = formData.tags
      .split(',')
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0)

    const submitData = {
      ...formData,
      sender_email: formData.sender_email || undefined,
      sender_name: formData.sender_name || undefined,
      subject_keywords: subject_keywords.length > 0 ? subject_keywords : undefined,
      exclude_keywords: exclude_keywords.length > 0 ? exclude_keywords : undefined,
      tags: tags.length > 0 ? tags : undefined
    }

    if (isEditing && newsletter) {
      updateMutation.mutate({ id: newsletter.id, data: submitData })
    } else {
      createMutation.mutate(submitData as GmailNewsletterCreate)
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

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">
              {isEditing ? 'Gmailニュースレター設定を編集' : '新しいGmailニュースレター設定を追加'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 基本設定 */}
            <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">基本設定</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    設定名 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="例: AI Weekly Newsletter"
                  />
                </div>

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
                    placeholder="例: ai, newsletter, weekly"
                  />
                </div>
              </div>
            </div>

            {/* フィルター設定 */}
            <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">メールフィルター設定</h3>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">送信者メールアドレス</label>
                    <input
                      type="email"
                      name="sender_email"
                      value={formData.sender_email}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="newsletter@example.com"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">送信者名</label>
                    <input
                      type="text"
                      name="sender_name"
                      value={formData.sender_name}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="AI Weekly"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    件名キーワード
                    <span className="text-sm text-gray-500 ml-2">（カンマ区切り、いずれかを含む）</span>
                  </label>
                  <input
                    type="text"
                    name="subject_keywords"
                    value={formData.subject_keywords}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="例: AI, machine learning, weekly"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    除外キーワード
                    <span className="text-sm text-gray-500 ml-2">（カンマ区切り、これらを含むものは除外）</span>
                  </label>
                  <input
                    type="text"
                    name="exclude_keywords"
                    value={formData.exclude_keywords}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="例: unsubscribe, spam, promotion"
                  />
                </div>
              </div>
            </div>

            {/* 取得設定 */}
            <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">取得設定</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">取得間隔（時間）</label>
                  <input
                    type="number"
                    name="fetch_interval_hours"
                    value={formData.fetch_interval_hours}
                    onChange={handleChange}
                    min="1"
                    max="168"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">1〜168時間（1週間）</p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">1回の最大取得数</label>
                  <input
                    type="number"
                    name="max_emails_per_fetch"
                    value={formData.max_emails_per_fetch}
                    onChange={handleChange}
                    min="1"
                    max="100"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">1〜100件</p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">遡る日数</label>
                  <input
                    type="number"
                    name="days_back"
                    value={formData.days_back}
                    onChange={handleChange}
                    min="1"
                    max="30"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">1〜30日</p>
                </div>
              </div>

              <div className="mt-4">
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
                    この設定を有効にする
                  </label>
                </div>
              </div>
            </div>

            {/* ボタン */}
            <div className="flex gap-4 pt-6 border-t border-gray-200 dark:border-gray-600">
              <button
                type="submit"
                disabled={isPending}
                className="btn-primary flex-1 disabled:opacity-50"
              >
                {isPending ? '保存中...' : (isEditing ? '更新' : '作成')}
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