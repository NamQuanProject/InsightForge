'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts'
import type { TrendResult } from '@/types'
import { 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Hash,
  Video,
  Eye,
  Heart,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  Zap
} from 'lucide-react'

interface TrendReportCardProps {
  trendResult: TrendResult
  index?: number
}

export function TrendReportCard({ trendResult, index = 0 }: TrendReportCardProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  const {
    main_keyword,
    why_the_trend_happens,
    trend_score,
    interest_over_day,
    avg_views_per_hour,
    recommended_action,
    top_videos,
    top_hashtags
  } = trendResult

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-emerald-600'
    if (score >= 40) return 'text-amber-600'
    return 'text-rose-600'
  }

  const getScoreBgColor = (score: number) => {
    if (score >= 70) return 'bg-emerald-500'
    if (score >= 40) return 'bg-amber-500'
    return 'bg-rose-500'
  }

  const getScoreRingColor = (score: number) => {
    if (score >= 70) return '#10b981'
    if (score >= 40) return '#f59e0b'
    return '#ef4444'
  }

  const getTrendIcon = (score: number) => {
    if (score >= 70) return <TrendingUp className="w-5 h-5 text-emerald-600" />
    if (score >= 40) return <Minus className="w-5 h-5 text-amber-600" />
    return <TrendingDown className="w-5 h-5 text-rose-600" />
  }

  const chartData = interest_over_day.map((value, index) => ({
    day: index + 1,
    interest: value
  }))

  const circumference = 2 * Math.PI * 40
  const strokeDashoffset = circumference - (trend_score / 100) * circumference

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toLocaleString()
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-6 border-b border-gray-100">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex items-start space-x-4">
            <div className="relative flex-shrink-0">
              <svg width="88" height="88" className="transform -rotate-90">
                <circle
                  cx="44"
                  cy="44"
                  r="36"
                  fill="none"
                  stroke="#e5e7eb"
                  strokeWidth="6"
                />
                <circle
                  cx="44"
                  cy="44"
                  r="36"
                  fill="none"
                  stroke={getScoreRingColor(trend_score)}
                  strokeWidth="6"
                  strokeLinecap="round"
                  strokeDasharray={2 * Math.PI * 36}
                  strokeDashoffset={2 * Math.PI * 36 - (trend_score / 100) * 2 * Math.PI * 36}
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-lg font-bold ${getScoreColor(trend_score)}`}>
                  {trend_score}
                </span>
                <span className="text-xs text-gray-400">/100</span>
              </div>
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs font-medium rounded">
                  #{index + 1}
                </span>
                {getTrendIcon(trend_score)}
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-1">
                {main_keyword}
              </h3>
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                <div className="flex items-center space-x-1">
                  <Eye className="w-4 h-4" />
                  <span>{formatNumber(avg_views_per_hour)} views/hour</span>
                </div>
              </div>
            </div>
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors self-start"
          >
            <span>{isExpanded ? 'Hide Details' : 'Show Details'}</span>
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="divide-y divide-gray-100">
          <div className="p-6">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Interest Over Time (Last 7 Days)</h4>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorInterest" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis 
                    dataKey="day" 
                    tick={{ fontSize: 12, fill: '#9ca3af' }}
                    tickLine={false}
                    axisLine={{ stroke: '#e5e7eb' }}
                    label={{ value: 'Day', position: 'bottom', offset: -5, fontSize: 12, fill: '#6b7280' }}
                  />
                  <YAxis 
                    tick={{ fontSize: 12, fill: '#9ca3af' }}
                    tickLine={false}
                    axisLine={{ stroke: '#e5e7eb' }}
                    tickFormatter={(value) => formatNumber(value)}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }}
                    formatter={(value) => {
                      if (typeof value === 'number') return [formatNumber(value), 'Interest']
                      if (Array.isArray(value) && typeof value[0] === 'number') return [formatNumber(value[0]), 'Interest']
                      return ['N/A', 'Interest']
                    }}
                    labelFormatter={(label) => `Day ${label}`}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="interest" 
                    stroke="#4f46e5" 
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorInterest)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="p-6">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Why This Trend Is Happening</h4>
            <div className="prose prose-sm max-w-none text-gray-700">
              <ReactMarkdown
                components={{
                  h1: ({ children }) => <h1 className="text-lg font-bold text-gray-900 mt-4 mb-2">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-base font-bold text-gray-900 mt-3 mb-2">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-sm font-bold text-gray-900 mt-2 mb-1">{children}</h3>,
                  p: ({ children }) => <p className="text-gray-700 leading-relaxed mb-3">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc list-inside text-gray-700 space-y-1 mb-3">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside text-gray-700 space-y-1 mb-3">{children}</ol>,
                  li: ({ children }) => <li className="text-gray-700">{children}</li>,
                  strong: ({ children }) => <strong className="font-bold text-gray-900">{children}</strong>,
                  em: ({ children }) => <em className="italic text-gray-700">{children}</em>,
                  code: ({ children }) => <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm text-indigo-600">{children}</code>,
                  blockquote: ({ children }) => <blockquote className="border-l-4 border-indigo-300 pl-3 italic text-gray-600 my-3">{children}</blockquote>,
                }}
              >
                {why_the_trend_happens}
              </ReactMarkdown>
            </div>
          </div>

          <div className="p-6">
            <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center space-x-2">
              <Zap className="w-4 h-4 text-indigo-600" />
              <span>Recommended Action</span>
            </h4>
            <div className="p-4 bg-indigo-50 border border-indigo-100 rounded-lg">
              <p className="text-sm text-indigo-800 leading-relaxed">
                {recommended_action}
              </p>
            </div>
          </div>

          {top_videos && top_videos.length > 0 && (
            <div className="p-6">
              <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center space-x-2">
                <Video className="w-4 h-4 text-rose-500" />
                <span>Top Performing Videos</span>
              </h4>
              <div className="space-y-3">
                {top_videos.slice(0, 3).map((video, idx) => (
                  <div key={video.video_id || idx} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="w-20 h-12 bg-gray-200 rounded-md flex-shrink-0 flex items-center justify-center">
                      {video.thumbnail_url ? (
                        <img 
                          src={video.thumbnail_url} 
                          alt={video.title}
                          className="w-full h-full object-cover rounded-md"
                        />
                      ) : (
                        <Video className="w-6 h-6 text-gray-400" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h5 className="text-sm font-medium text-gray-900 truncate">
                        {video.title}
                      </h5>
                      <div className="flex items-center space-x-3 mt-1 text-xs text-gray-500">
                        <span className="flex items-center space-x-1">
                          <Eye className="w-3 h-3" />
                          <span>{formatNumber(video.views)}</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <Heart className="w-3 h-3" />
                          <span>{formatNumber(video.likes)}</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <MessageSquare className="w-3 h-3" />
                          <span>{formatNumber(video.comments)}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {top_hashtags && top_hashtags.length > 0 && (
            <div className="p-6">
              <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center space-x-2">
                <Hash className="w-4 h-4 text-indigo-600" />
                <span>Top Hashtags</span>
              </h4>
              <div className="flex flex-wrap gap-2">
                {top_hashtags.map((hashtag, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center px-3 py-1.5 bg-gray-100 text-gray-700 text-sm font-medium rounded-full hover:bg-indigo-100 hover:text-indigo-700 transition-colors cursor-default"
                  >
                    <Hash className="w-3.5 h-3.5 mr-0.5" />
                    {hashtag.replace('#', '')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}