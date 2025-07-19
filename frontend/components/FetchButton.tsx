'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { triggerNewsFetch } from '@/lib/api'

interface FetchButtonProps {
  onSuccess?: () => void
}

export default function FetchButton({ onSuccess }: FetchButtonProps) {
  const [isLoading, setIsLoading] = useState(false)

  const fetchMutation = useMutation({
    mutationFn: triggerNewsFetch,
    onMutate: () => setIsLoading(true),
    onSuccess: () => {
      alert('News fetching started in background!')
      onSuccess?.()
    },
    onError: (error) => {
      alert('Failed to start news fetching')
      console.error(error)
    },
    onSettled: () => setIsLoading(false),
  })

  return (
    <button
      onClick={() => fetchMutation.mutate()}
      disabled={isLoading}
      className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {isLoading ? 'Fetching...' : 'Fetch News'}
    </button>
  )
}