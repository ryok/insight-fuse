interface SourceFilterProps {
  value: string
  onChange: (value: string) => void
}

const sources = [
  { value: '', label: 'All Sources' },
  { value: 'techcrunch', label: 'TechCrunch' },
  { value: 'ars-technica', label: 'Ars Technica' },
  { value: 'the-verge', label: 'The Verge' },
  { value: 'hacker-news', label: 'Hacker News' },
]

export default function SourceFilter({ value, onChange }: SourceFilterProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
    >
      {sources.map((source) => (
        <option key={source.value} value={source.value}>
          {source.label}
        </option>
      ))}
    </select>
  )
}