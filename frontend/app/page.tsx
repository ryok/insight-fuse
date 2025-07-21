'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import ArticleList from '@/components/ArticleList'
import LanguageFilter from '@/components/LanguageFilter'
import SourceFilter from '@/components/SourceFilter'
import FetchButton from '@/components/FetchButton'
import { fetchArticles } from '@/lib/api'

export default function Home() {
  const [selectedLanguage, setSelectedLanguage] = useState<string>('')
  const [selectedSource, setSelectedSource] = useState<string>('')

  const { data: articles, isLoading, refetch } = useQuery({
    queryKey: ['articles', selectedLanguage, selectedSource],
    queryFn: () => fetchArticles({ language: selectedLanguage, source: selectedSource }),
  })

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            InsightFuse
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            AI-powered news aggregation and analysis platform
          </p>
        </header>

        <div className="mb-8 flex flex-wrap gap-4 items-center">
          <LanguageFilter
            value={selectedLanguage}
            onChange={setSelectedLanguage}
          />
          <SourceFilter
            value={selectedSource}
            onChange={setSelectedSource}
          />
          <FetchButton onSuccess={() => refetch()} />
          
          <div className="ml-auto flex gap-4">
            <Link
              href="/custom-sites"
              className="text-primary-500 hover:text-primary-600 text-sm"
            >
              カスタムサイト管理 →
            </Link>
            <Link
              href="/gmail"
              className="text-primary-500 hover:text-primary-600 text-sm"
            >
              Gmail設定 →
            </Link>
          </div>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
          </div>
        ) : (
          <ArticleList articles={articles || []} />
        )}
      </div>
    </main>
  )
}