'use client'

import { useState } from 'react'
import { 
  Play, 
  Clock, 
  Video, 
  ChevronDown, 
  ChevronUp,
  Mic,
  Monitor,
  Zap
} from 'lucide-react'
import type { VideoScript, VideoScriptSection } from '@/types'

interface VideoScriptPreviewProps {
  videoScript: VideoScript
  title?: string
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

function estimateSectionTiming(
  index: number, 
  totalSections: number, 
  totalDuration: number
): { start: number; end: number } {
  const sectionDuration = Math.floor(totalDuration / totalSections)
  const start = index * sectionDuration
  const end = index === totalSections - 1 ? totalDuration : (index + 1) * sectionDuration
  return { start, end }
}

export function VideoScriptPreview({ videoScript, title }: VideoScriptPreviewProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  const {
    intro,
    hook,
    main_content = [],
    sections = [],
    call_to_action,
    duration_estimate_seconds
  } = videoScript

  const displayTitle = title || 'Video Script Preview'

  const allSections: Array<{
    timestamp_start: number
    timestamp_end: number
    label: string
    narration: string
    visual_description?: string
    isGenerated: boolean
  }> = []

  if (sections && sections.length > 0) {
    sections.forEach((section) => {
      allSections.push({
        timestamp_start: section.timestamp_start_seconds,
        timestamp_end: section.timestamp_end_seconds,
        label: section.label,
        narration: section.narration,
        visual_description: section.visual_description,
        isGenerated: false
      })
    })
  } else if (main_content && main_content.length > 0) {
    main_content.forEach((content, index) => {
      const timing = estimateSectionTiming(
        index, 
        main_content.length + 2,
        duration_estimate_seconds
      )
      allSections.push({
        timestamp_start: timing.start,
        timestamp_end: timing.end,
        label: `Section ${index + 1}`,
        narration: content,
        isGenerated: true
      })
    })
  }

  if (hook) {
    const hookTiming = estimateSectionTiming(0, allSections.length + 2, duration_estimate_seconds)
    allSections.unshift({
      timestamp_start: 0,
      timestamp_end: Math.floor(duration_estimate_seconds * 0.15),
      label: 'Hook',
      narration: hook,
      isGenerated: true
    })
  }

  if (call_to_action) {
    const ctaStart = Math.floor(duration_estimate_seconds * 0.85)
    allSections.push({
      timestamp_start: ctaStart,
      timestamp_end: duration_estimate_seconds,
      label: 'Call to Action',
      narration: call_to_action,
      isGenerated: true
    })
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-6 border-b border-gray-100">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex items-start space-x-4">
            <div className="w-14 h-14 bg-gradient-to-br from-rose-500 to-orange-500 rounded-xl flex items-center justify-center flex-shrink-0">
              <Video className="w-7 h-7 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                {displayTitle}
              </h2>
              <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                <div className="flex items-center space-x-1.5">
                  <Clock className="w-4 h-4" />
                  <span>{formatTime(duration_estimate_seconds)} total</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <Mic className="w-4 h-4" />
                  <span>{allSections.length} segments</span>
                </div>
              </div>
            </div>
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 rounded-lg transition-colors self-start"
          >
            <span>{isExpanded ? 'Collapse' : 'Expand'}</span>
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>

        {hook && (
          <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <Zap className="w-4 h-4 text-amber-600" />
              <span className="text-sm font-semibold text-amber-800">Hook</span>
            </div>
            <p className="text-amber-900 leading-relaxed">
              {hook}
            </p>
          </div>
        )}
      </div>

      {isExpanded && (
        <div className="divide-y divide-gray-100">
          {allSections.map((section, index) => (
            <div 
              key={index}
              className="p-5 hover:bg-gray-50 transition-colors"
            >
              <div className="flex flex-col lg:flex-row lg:items-start gap-4">
                <div className="flex-shrink-0 flex lg:flex-col items-center lg:items-start space-x-3 lg:space-x-0 lg:space-y-2">
                  <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-mono font-medium ${
                    section.label === 'Hook' 
                      ? 'bg-amber-100 text-amber-800' 
                      : section.label === 'Call to Action'
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-indigo-100 text-indigo-800'
                  }`}>
                    <Play className="w-3 h-3 mr-1" />
                    {formatTime(section.timestamp_start)} - {formatTime(section.timestamp_end)}
                  </span>
                  <span className="text-xs text-gray-400">
                    {formatTime(section.timestamp_end - section.timestamp_start)}
                  </span>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-2">
                    <h4 className={`text-sm font-semibold ${
                      section.label === 'Hook' 
                        ? 'text-amber-700' 
                        : section.label === 'Call to Action'
                        ? 'text-emerald-700'
                        : 'text-gray-900'
                    }`}>
                      {section.label}
                    </h4>
                    <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded font-medium">
                      Scene {index + 1}
                    </span>
                  </div>

                  <div className="mb-4">
                    <div className="flex items-center space-x-1.5 mb-1.5">
                      <Mic className="w-3.5 h-3.5 text-indigo-500" />
                      <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Narration</span>
                    </div>
                    <p className="text-sm text-gray-700 leading-relaxed pl-5 border-l-2 border-indigo-200">
                      {section.narration}
                    </p>
                  </div>

                  {section.visual_description && (
                    <div>
                      <div className="flex items-center space-x-1.5 mb-1.5">
                        <Monitor className="w-3.5 h-3.5 text-emerald-500" />
                        <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Visual</span>
                      </div>
                      <p className="text-sm text-gray-600 leading-relaxed pl-5 border-l-2 border-emerald-200">
                        {section.visual_description}
                      </p>
                    </div>
                  )}
                </div>

                <div className="flex-shrink-0 w-full lg:w-48">
                  <div className="relative">
                    <div className="w-full h-28 bg-gray-100 rounded-lg flex flex-col items-center justify-center border-2 border-dashed border-gray-200 hover:border-indigo-300 transition-colors">
                      <Video className="w-8 h-8 text-gray-300 mb-1" />
                      <span className="text-xs text-gray-400">Thumbnail</span>
                    </div>
                    <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded font-mono">
                      {formatTime(section.timestamp_end - section.timestamp_start)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="p-4 bg-gray-50 border-t border-gray-100">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <div className="flex items-center space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-amber-500" />
              <span>Hook</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
              <span>Content</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              <span>CTA</span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-200 rounded-lg transition-colors">
              Edit Script
            </button>
            <button className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors flex items-center space-x-2">
              <Play className="w-4 h-4" />
              <span>Generate Video</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}