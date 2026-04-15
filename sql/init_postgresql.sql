CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    name TEXT,
    plan TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trend_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed',
    results JSONB NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    error JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS generated_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    trend_analysis_id UUID REFERENCES trend_analyses(id) ON DELETE SET NULL,
    selected_keyword TEXT,
    main_title TEXT,
    video_script JSONB NOT NULL,
    platform_posts JSONB NOT NULL,
    thumbnail JSONB,
    music_background TEXT,
    raw_output JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'generated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS publish_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    generated_content_id UUID REFERENCES generated_contents(id) ON DELETE SET NULL,
    profile_username TEXT NOT NULL,
    platforms JSONB NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    first_comment TEXT,
    schedule_post TEXT,
    link_url TEXT,
    subreddit TEXT,
    asset_urls JSONB NOT NULL DEFAULT '[]'::jsonb,
    uploaded_files JSONB NOT NULL DEFAULT '[]'::jsonb,
    post_kind TEXT NOT NULL DEFAULT 'text',
    provider_request_id TEXT,
    provider_job_id TEXT,
    provider_response JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'submitted',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trend_analyses_user_id ON trend_analyses (user_id);
CREATE INDEX IF NOT EXISTS idx_trend_analyses_created_at ON trend_analyses (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generated_contents_user_id ON generated_contents (user_id);
CREATE INDEX IF NOT EXISTS idx_generated_contents_trend_analysis_id ON generated_contents (trend_analysis_id);
CREATE INDEX IF NOT EXISTS idx_publish_jobs_user_id ON publish_jobs (user_id);
CREATE INDEX IF NOT EXISTS idx_publish_jobs_generated_content_id ON publish_jobs (generated_content_id);
CREATE INDEX IF NOT EXISTS idx_publish_jobs_profile_username ON publish_jobs (profile_username);
CREATE INDEX IF NOT EXISTS idx_publish_jobs_status ON publish_jobs (status);
