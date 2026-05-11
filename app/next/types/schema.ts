export interface TrendResult {
  main_keyword: string
  why_the_trend_happens: string
  trend_score: number
  interest_over_day: number[]
  avg_views_per_hour: number
  recommended_action: string
  top_videos: TopVideo[]
  top_hashtags: string[]
}

export interface TopVideo {
  video_id: string
  title: string
  views: number
  likes: number
  comments: number
  published_at: string
  thumbnail_url?: string
}

export interface TrendReport {
  query: string
  results: TrendResult[]
  markdown_summary: string
  generated_at: string
}

export interface ContentBundle {
  selected_keyword: string
  main_title: string
  video_script: VideoScript
  platform_posts: PlatformPost[]
  music_background: MusicBackground
}

export interface VideoScript {
  intro: string
  hook: string
  main_content: string[]
  call_to_action: string
  duration_estimate_seconds: number
}

export interface PlatformPost {
  platform: 'youtube' | 'tiktok' | 'instagram' | 'x' | 'linkedin'
  title?: string
  content: string
  hashtags: string[]
  scheduled_for?: string
}

export interface MusicBackground {
  genre: string
  mood: string
  recommended_artists?: string[]
  tempo_bpm: number
}

export interface OrchestrationResponse {
  success: boolean
  task_id: string
  message: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  trend_report?: TrendReport
  content_bundle?: ContentBundle
}

export interface OrchestrationTask {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  query: string
  created_at: string
  completed_at?: string
  result?: {
    trend_report?: TrendReport
    content_bundle?: ContentBundle
  }
  error?: string
}