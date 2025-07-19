import Link from 'next/link'
import { format } from 'date-fns'
import { Article } from '@/lib/api'

interface ArticleListProps {
  articles: Article[]
}

export default function ArticleList({ articles }: ArticleListProps) {
  if (articles.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">
          No articles found. Try fetching new articles.
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {articles.map((article) => (
        <Link
          key={article.id}
          href={`/article/${article.id}`}
          className="card hover:shadow-lg transition-shadow"
        >
          <div className="space-y-3">
            <h2 className="text-xl font-semibold line-clamp-2">
              {article.title}
            </h2>
            
            {article.description && (
              <p className="text-gray-600 dark:text-gray-400 line-clamp-3">
                {article.description}
              </p>
            )}
            
            <div className="flex justify-between items-center text-sm text-gray-500 dark:text-gray-400">
              <span className="capitalize">{article.source}</span>
              <time dateTime={article.published_at}>
                {format(new Date(article.published_at), 'MMM d, yyyy')}
              </time>
            </div>
            
            {article.tags && article.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {article.tags.slice(0, 3).map((tag, index) => (
                  <span
                    key={index}
                    className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-1 rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </Link>
      ))}
    </div>
  )
}