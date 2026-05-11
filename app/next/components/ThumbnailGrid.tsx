'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import { 
  Image as ImageIcon, 
  Download, 
  Trash2, 
  Maximize2,
  CheckCircle2
} from 'lucide-react'

interface ThumbnailGridProps {
  images: {
    url: string
    alt?: string
    isSelected?: boolean
    onSelect?: (url: string) => void
    onDelete?: (url: string) => void
    onDownload?: (url: string) => void
  }[]
  columns?: 2 | 3 | 4
  showActions?: boolean
  onImageClick?: (url: string, index: number) => void
}

function ShimmerSkeleton() {
  return (
    <div className="relative overflow-hidden bg-gray-100 rounded-lg aspect-video">
      <div className="absolute inset-0 bg-gradient-to-r from-gray-100 via-white to-gray-100" 
           style={{ animation: 'shimmer 1.5s infinite' }} />
      <style jsx>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  )
}

function ImageCard({ 
  image, 
  index,
  showActions,
  onImageClick
}: { 
  image: ThumbnailGridProps['images'][0]
  index: number
  showActions: boolean
  onImageClick?: (url: string, index: number) => void
}) {
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [isHovered, setIsHovered] = useState(false)

  const handleLoad = () => setIsLoading(false)
  const handleError = () => {
    setIsLoading(false)
    setHasError(true)
  }

  const handleClick = () => {
    onImageClick?.(image.url, index)
  }

  return (
    <div 
      className="relative group"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {isLoading && !hasError && (
        <div className="absolute inset-0 z-10">
          <ShimmerSkeleton />
        </div>
      )}

      {hasError ? (
        <div className="aspect-video bg-gray-50 rounded-lg border border-dashed border-gray-200 flex flex-col items-center justify-center">
          <ImageIcon className="w-8 h-8 text-gray-300 mb-2" />
          <p className="text-xs text-gray-400">Failed to load</p>
        </div>
      ) : (
        <div 
          className={`aspect-video relative rounded-lg overflow-hidden cursor-pointer transition-all duration-200 ${
            image.isSelected 
              ? 'ring-2 ring-indigo-500 ring-offset-2' 
              : 'hover:ring-2 hover:ring-gray-200 hover:ring-offset-2'
          }`}
          onClick={handleClick}
        >
          <Image
            src={image.url}
            alt={image.alt || `Generated thumbnail ${index + 1}`}
            fill
            className={`object-cover transition-transform duration-300 ${
              isHovered ? 'scale-105' : 'scale-100'
            }`}
            loading="lazy"
            onLoad={handleLoad}
            onError={handleError}
            sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw"
            placeholder="empty"
          />

          {image.isSelected && (
            <div className="absolute top-2 right-2 z-20">
              <div className="bg-indigo-600 rounded-full p-1.5 shadow-lg">
                <CheckCircle2 className="w-4 h-4 text-white" />
              </div>
            </div>
          )}

          {showActions && isHovered && (
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent p-3 z-20">
              <div className="flex items-center justify-end space-x-2">
                {image.onDownload && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      image.onDownload?.(image.url)
                    }}
                    className="p-2 bg-white/20 hover:bg-white/30 rounded-lg backdrop-blur-sm transition-colors"
                    title="Download"
                  >
                    <Download className="w-4 h-4 text-white" />
                  </button>
                )}
                {image.onDelete && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      image.onDelete?.(image.url)
                    }}
                    className="p-2 bg-white/20 hover:bg-red-500/70 rounded-lg backdrop-blur-sm transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4 text-white" />
                  </button>
                )}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onImageClick?.(image.url, index)
                  }}
                  className="p-2 bg-white/20 hover:bg-white/30 rounded-lg backdrop-blur-sm transition-colors"
                  title="View full size"
                >
                  <Maximize2 className="w-4 h-4 text-white" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function ThumbnailGrid({
  images,
  columns = 3,
  showActions = true,
  onImageClick
}: ThumbnailGridProps) {
  const [skeletonCount] = useState(images.length || 6)

  const getGridCols = () => {
    switch (columns) {
      case 2:
        return 'grid-cols-1 md:grid-cols-2'
      case 4:
        return 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4'
      case 3:
      default:
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
    }
  }

  if (!images || images.length === 0) {
    return (
      <div className="grid gap-4 md:gap-6" style={{ animation: 'none' }}>
        <style>{`
          @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
          }
        `}</style>
        {Array.from({ length: skeletonCount }).map((_, index) => (
          <div key={index} className="col-span-1">
            <ShimmerSkeleton />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div 
      className={`grid gap-4 md:gap-6 ${getGridCols()}`}
      style={{ animation: 'none' }}
    >
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>
      {images.map((image, index) => (
        <ImageCard
          key={`${image.url}-${index}`}
          image={image}
          index={index}
          showActions={showActions}
          onImageClick={onImageClick}
        />
      ))}
    </div>
  )
}

export default ThumbnailGrid