'use client'

import { useState } from 'react'

interface QueryInputProps {
  onSubmit?: (query: string) => void | Promise<void>
  placeholder?: string
}

export function QueryInput({ 
  onSubmit,
  placeholder = "Describe what content you'd like to generate. For example: 'Generate a Q4 sales report with revenue breakdown and top performing products.'"
}: QueryInputProps) {
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!query.trim() || isLoading) return

    setIsLoading(true)
    
    try {
      await onSubmit?.(query.trim())
    } catch (error) {
      console.error('Query submission error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            disabled={isLoading}
            rows={5}
            className="w-full px-4 py-4 bg-white border border-gray-300 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed text-base"
          />
          <div className="absolute bottom-4 right-4 flex items-center space-x-2 text-xs text-gray-400">
            <span>{query.length} characters</span>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="text-xs text-gray-500">
            <span className="font-medium text-indigo-600">Tip:</span> Be specific about the type of content, tone, and audience for better results.
          </div>
          
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="inline-flex items-center justify-center space-x-2 px-8 py-3 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-indigo-600"
          >
            {isLoading ? (
              <>
                <div className="relative">
                  <div className="w-5 h-5 border-2 border-indigo-300 rounded-full animate-spin" />
                  <div className="absolute top-0 left-0 w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" style={{ animationDuration: '0.8s' }} />
                </div>
                <span>Generating...</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>Generate</span>
              </>
            )}
          </button>
        </div>
      </form>

      {isLoading && (
        <div className="mt-8 p-6 bg-gradient-to-r from-indigo-50 to-emerald-50 rounded-xl border border-indigo-100">
          <div className="flex flex-col items-center text-center space-y-4">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-indigo-200 rounded-full" />
              <div className="absolute top-0 left-0 w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" style={{ animationDuration: '1s' }} />
              <div className="absolute top-2 left-2 w-12 h-12 border-4 border-emerald-400 border-b-transparent border-l-transparent rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }} />
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-gray-900">
                Analyzing trends and generating content...
              </h3>
              <p className="text-sm text-gray-600">
                This may take up to 90 seconds
              </p>
            </div>

            <div className="flex items-center space-x-3 pt-2">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-xs text-gray-500">Processing your request</span>
            </div>

            <div className="w-full max-w-md pt-2">
              <div className="bg-gray-200 rounded-full h-1.5 overflow-hidden">
                <div className="bg-gradient-to-r from-indigo-500 to-emerald-500 h-full rounded-full animate-pulse" style={{ width: '60%', animationDuration: '2s' }} />
              </div>
              <div className="flex justify-between mt-1 text-xs text-gray-400">
                <span>Analyzing query</span>
                <span>Generating content</span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 pt-4 w-full max-w-md">
              <div className="bg-white/60 rounded-lg p-2.5 text-center border border-indigo-100/50">
                <div className="w-6 h-6 mx-auto mb-1 flex items-center justify-center">
                  <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
                </div>
                <p className="text-xs text-gray-600 font-medium">Analyzing</p>
              </div>
              <div className="bg-white/60 rounded-lg p-2.5 text-center border border-indigo-100/50 opacity-60">
                <div className="w-6 h-6 mx-auto mb-1 flex items-center justify-center">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <p className="text-xs text-gray-600 font-medium">Drafting</p>
              </div>
              <div className="bg-white/60 rounded-lg p-2.5 text-center border border-indigo-100/50 opacity-60">
                <div className="w-6 h-6 mx-auto mb-1 flex items-center justify-center">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-xs text-gray-600 font-medium">Polishing</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}