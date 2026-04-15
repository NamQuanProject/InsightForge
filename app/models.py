import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plan: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    trend_analyses: Mapped[list["TrendAnalysis"]] = relationship(back_populates="user")
    generated_contents: Mapped[list["GeneratedContent"]] = relationship(back_populates="user")
    publish_jobs: Mapped[list["PublishJob"]] = relationship(back_populates="user")


class TrendAnalysis(Base):
    __tablename__ = "trend_analyses"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    query: Mapped[str] = mapped_column(Text())
    status: Mapped[str] = mapped_column(String(50), default="completed")
    results: Mapped[list[dict]] = mapped_column(JSONB)
    summary: Mapped[str] = mapped_column(Text(), default="")
    error: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User | None] = relationship(back_populates="trend_analyses")
    generated_contents: Mapped[list["GeneratedContent"]] = relationship(back_populates="trend_analysis")


class GeneratedContent(Base):
    __tablename__ = "generated_contents"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    trend_analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("trend_analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    selected_keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
    main_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_script: Mapped[dict | list] = mapped_column(JSONB)
    platform_posts: Mapped[dict] = mapped_column(JSONB)
    thumbnail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    music_background: Mapped[str | None] = mapped_column(Text(), nullable=True)
    raw_output: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="generated")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User | None] = relationship(back_populates="generated_contents")
    trend_analysis: Mapped[TrendAnalysis | None] = relationship(back_populates="generated_contents")
    publish_jobs: Mapped[list["PublishJob"]] = relationship(back_populates="generated_content")


class PublishJob(Base):
    __tablename__ = "publish_jobs"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    generated_content_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("generated_contents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    profile_username: Mapped[str] = mapped_column(String(255), index=True)
    platforms: Mapped[list[str]] = mapped_column(JSONB)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    first_comment: Mapped[str | None] = mapped_column(Text(), nullable=True)
    schedule_post: Mapped[str | None] = mapped_column(String(100), nullable=True)
    link_url: Mapped[str | None] = mapped_column(Text(), nullable=True)
    subreddit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    asset_urls: Mapped[list[str]] = mapped_column(JSONB, default=list)
    uploaded_files: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    post_kind: Mapped[str] = mapped_column(String(50), default="text")
    provider_request_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    provider_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    provider_response: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="submitted", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User | None] = relationship(back_populates="publish_jobs")
    generated_content: Mapped[GeneratedContent | None] = relationship(back_populates="publish_jobs")
