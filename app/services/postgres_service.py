import uuid
from typing import Any

from sqlalchemy import select

from app.db import get_session_factory
from app.models import GeneratedContent, TrendAnalysis, User


class PostgresService:
    async def create_user(self, email: str, name: str | None = None, plan: str | None = None) -> User:
        async with get_session_factory()() as session:
            user = User(email=email, name=name, plan=plan)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def list_users(self) -> list[User]:
        async with get_session_factory()() as session:
            result = await session.execute(select(User).order_by(User.created_at.desc()))
            return list(result.scalars().all())

    async def get_user(self, user_id: uuid.UUID | str) -> User | None:
        parsed_id = self._coerce_uuid(user_id)
        async with get_session_factory()() as session:
            return await session.get(User, parsed_id)

    async def save_trend_analysis(
        self,
        query: str,
        results: list[dict[str, Any]],
        summary: str = "",
        user_id: uuid.UUID | str | None = None,
        status: str = "completed",
        error: dict[str, Any] | None = None,
    ) -> TrendAnalysis:
        async with get_session_factory()() as session:
            analysis = TrendAnalysis(
                user_id=self._coerce_uuid(user_id) if user_id else None,
                query=query,
                status=status,
                results=results,
                summary=summary,
                error=error,
            )
            session.add(analysis)
            await session.commit()
            await session.refresh(analysis)
            return analysis

    async def list_trend_analyses(
        self,
        user_id: uuid.UUID | str | None = None,
        limit: int = 20,
    ) -> list[TrendAnalysis]:
        async with get_session_factory()() as session:
            statement = select(TrendAnalysis).order_by(TrendAnalysis.created_at.desc()).limit(limit)
            if user_id:
                statement = statement.where(TrendAnalysis.user_id == self._coerce_uuid(user_id))
            result = await session.execute(statement)
            return list(result.scalars().all())

    async def get_trend_analysis(self, analysis_id: uuid.UUID | str) -> TrendAnalysis | None:
        parsed_id = self._coerce_uuid(analysis_id)
        async with get_session_factory()() as session:
            return await session.get(TrendAnalysis, parsed_id)

    async def save_generated_content(
        self,
        raw_output: dict[str, Any],
        video_script: dict[str, Any] | list[Any],
        platform_posts: dict[str, Any],
        thumbnail: dict[str, Any] | None,
        user_id: uuid.UUID | str | None = None,
        trend_analysis_id: uuid.UUID | str | None = None,
        selected_keyword: str | None = None,
        main_title: str | None = None,
        music_background: str | None = None,
        status: str = "generated",
    ) -> GeneratedContent:
        async with get_session_factory()() as session:
            content = GeneratedContent(
                user_id=self._coerce_uuid(user_id) if user_id else None,
                trend_analysis_id=self._coerce_uuid(trend_analysis_id) if trend_analysis_id else None,
                selected_keyword=selected_keyword,
                main_title=main_title,
                video_script=video_script,
                platform_posts=platform_posts,
                thumbnail=thumbnail,
                music_background=music_background,
                raw_output=raw_output,
                status=status,
            )
            session.add(content)
            await session.commit()
            await session.refresh(content)
            return content

    async def list_generated_contents(
        self,
        user_id: uuid.UUID | str | None = None,
        limit: int = 20,
    ) -> list[GeneratedContent]:
        async with get_session_factory()() as session:
            statement = select(GeneratedContent).order_by(GeneratedContent.created_at.desc()).limit(limit)
            if user_id:
                statement = statement.where(GeneratedContent.user_id == self._coerce_uuid(user_id))
            result = await session.execute(statement)
            return list(result.scalars().all())

    async def get_generated_content(self, content_id: uuid.UUID | str) -> GeneratedContent | None:
        parsed_id = self._coerce_uuid(content_id)
        async with get_session_factory()() as session:
            return await session.get(GeneratedContent, parsed_id)

    def _coerce_uuid(self, value: uuid.UUID | str) -> uuid.UUID:
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))
