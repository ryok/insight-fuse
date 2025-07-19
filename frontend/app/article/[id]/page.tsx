'use client'

import { useQuery, useMutation } from '@tanstack/react-query'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { format } from 'date-fns'
import ReactMarkdown from 'react-markdown'
import {
  fetchArticle,
  fetchSummaries,
  fetchAnalysis,
  createSummary,
  createAnalysis,
} from '@/lib/api'

export default function ArticlePage() {
  const params = useParams()
  const articleId = Number(params.id)

  const { data: article, isLoading } = useQuery({
    queryKey: ['article', articleId],
    queryFn: () => fetchArticle(articleId),
  })

  const { data: summaries, refetch: refetchSummaries } = useQuery({
    queryKey: ['summaries', articleId],
    queryFn: () => fetchSummaries(articleId),
    enabled: !!article,
  })

  const { data: analysis, refetch: refetchAnalysis } = useQuery({
    queryKey: ['analysis', articleId],
    queryFn: () => fetchAnalysis(articleId),
    enabled: !!article,
  })

  const createSummaryMutation = useMutation({
    mutationFn: (language: string) => createSummary(articleId, language),
    onSuccess: () => refetchSummaries(),
  })

  const createAnalysisMutation = useMutation({
    mutationFn: () => createAnalysis(articleId),
    onSuccess: () => refetchAnalysis(),
  })

  if (isLoading || !article) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Link
          href="/"
          className="inline-flex items-center text-primary-500 hover:text-primary-600 mb-6"
        >
          ← Back to Articles
        </Link>

        <article className="card mb-8">
          <header className="mb-6">
            <h1 className="text-3xl font-bold mb-4">{article.title}</h1>
            <div className="flex justify-between items-center text-gray-600 dark:text-gray-400">
              <div>
                <span className="capitalize">{article.source}</span>
                {article.author && <span> • By {article.author}</span>}
              </div>
              <time dateTime={article.published_at}>
                {format(new Date(article.published_at), 'MMMM d, yyyy')}
              </time>
            </div>
          </header>

          {article.description && (
            <p className="text-lg text-gray-700 dark:text-gray-300 mb-6">
              {article.description}
            </p>
          )}

          {article.content && (
            <div className="prose dark:prose-invert max-w-none">
              <ReactMarkdown>{article.content}</ReactMarkdown>
            </div>
          )}

          {article.source_url && (
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <a
                href={article.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-500 hover:text-primary-600"
              >
                Read original article →
              </a>
            </div>
          )}
        </article>

        <div className="space-y-6">
          <section className="card">
            <h2 className="text-2xl font-bold mb-4">Summaries</h2>
            <div className="space-y-4">
              <div className="flex gap-2">
                <button
                  onClick={() => createSummaryMutation.mutate('en')}
                  disabled={createSummaryMutation.isPending}
                  className="btn-secondary"
                >
                  Generate English Summary
                </button>
                <button
                  onClick={() => createSummaryMutation.mutate('ja')}
                  disabled={createSummaryMutation.isPending}
                  className="btn-secondary"
                >
                  日本語要約を生成
                </button>
              </div>

              {summaries && summaries.length > 0 && (
                <div className="space-y-4">
                  {summaries.map((summary) => (
                    <div
                      key={summary.id}
                      className="border-l-4 border-primary-500 pl-4"
                    >
                      <h3 className="font-semibold mb-2">
                        {summary.language === 'ja' ? '日本語要約' : 'English Summary'}
                      </h3>
                      <p className="text-gray-700 dark:text-gray-300 mb-2">
                        {summary.summary_text}
                      </p>
                      {summary.key_points.length > 0 && (
                        <ul className="list-disc list-inside text-gray-600 dark:text-gray-400">
                          {summary.key_points.map((point, index) => (
                            <li key={index}>{point}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="card">
            <h2 className="text-2xl font-bold mb-4">AI Analysis</h2>
            <button
              onClick={() => createAnalysisMutation.mutate()}
              disabled={createAnalysisMutation.isPending || !!analysis}
              className="btn-primary mb-4"
            >
              {analysis ? 'Analysis Generated' : 'Generate Analysis'}
            </button>

            {analysis && (
              <div className="space-y-6">
                {Object.keys(analysis.vocabulary_analysis).length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-2">
                      Vocabulary (TOEIC 800+ Level)
                    </h3>
                    <dl className="space-y-2">
                      {Object.entries(analysis.vocabulary_analysis).map(
                        ([word, explanation]) => (
                          <div key={word}>
                            <dt className="font-medium inline">{word}:</dt>
                            <dd className="inline ml-2 text-gray-600 dark:text-gray-400">
                              {explanation}
                            </dd>
                          </div>
                        )
                      )}
                    </dl>
                  </div>
                )}

                {analysis.context_explanation && (
                  <div>
                    <h3 className="text-lg font-semibold mb-2">背景説明</h3>
                    <p className="text-gray-700 dark:text-gray-300">
                      {analysis.context_explanation}
                    </p>
                  </div>
                )}

                {analysis.impact_analysis && (
                  <div>
                    <h3 className="text-lg font-semibold mb-2">今後の影響</h3>
                    <p className="text-gray-700 dark:text-gray-300">
                      {analysis.impact_analysis}
                    </p>
                  </div>
                )}

                {analysis.blog_titles.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-2">
                      ブログ・SNS投稿タイトル案
                    </h3>
                    <ul className="list-disc list-inside space-y-1">
                      {analysis.blog_titles.map((title, index) => (
                        <li key={index} className="text-gray-700 dark:text-gray-300">
                          {title}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  )
}