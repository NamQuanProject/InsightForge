import uuid
from typing import Any

from sqlalchemy import func, select

from app.db import get_session_factory
from app.models import GeneratedContent, PublishJob, TrendAnalysis, User
from app.schema.user import UserResponse, UserSummaryResponse


class PostgresService:
    async def create_user(
        self,
        email: str,
        name: str | None = None,
        plan: str | None = None,
        upload_post_account: dict[str, Any] | None = None,
        profiles: list[dict[str, Any]] | None = None,
        social_accounts: dict[str, Any] | None = None,
        connected_platforms: list[str] | None = None,
    ) -> User:
        async with get_session_factory()() as session:
            user = User(
                email=email,
                name=name,
                plan=plan,
                upload_post_account=upload_post_account or {},
                profiles=profiles or [],
                social_accounts=social_accounts or {},
                connected_platforms=connected_platforms or [],
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def upsert_user(
        self,
        email: str,
        name: str | None = None,
        plan: str | None = None,
        upload_post_account: dict[str, Any] | None = None,
        profiles: list[dict[str, Any]] | None = None,
        social_accounts: dict[str, Any] | None = None,
        connected_platforms: list[str] | None = None,
    ) -> User:
        async with get_session_factory()() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user is None:
                user = User(
                    email=email,
                    name=name,
                    plan=plan,
                    upload_post_account=upload_post_account or {},
                    profiles=profiles or [],
                    social_accounts=social_accounts or {},
                    connected_platforms=connected_platforms or [],
                )
                session.add(user)
            else:
                if name is not None:
                    user.name = name
                if plan is not None:
                    user.plan = plan
                if upload_post_account is not None:
                    user.upload_post_account = upload_post_account
                if profiles is not None:
                    user.profiles = profiles
                if social_accounts is not None:
                    user.social_accounts = social_accounts
                if connected_platforms is not None:
                    user.connected_platforms = connected_platforms

            await session.commit()
            await session.refresh(user)
            return user

    async def list_users(self) -> list[User]:
        async with get_session_factory()() as session:
            result = await session.execute(select(User).order_by(User.created_at.desc()))
            return list(result.scalars().all())

    async def list_user_summaries(self) -> list[UserSummaryResponse]:
        async with get_session_factory()() as session:
            result = await session.execute(select(User).order_by(User.created_at.desc()))
            users = list(result.scalars().all())
            summaries: list[UserSummaryResponse] = []
            for user in users:
                summaries.append(
                    UserSummaryResponse(
                        **self._user_payload(user),
                        trend_analysis_count=await self._count_for_user(session, TrendAnalysis, user.id),
                        generated_content_count=await self._count_for_user(session, GeneratedContent, user.id),
                        publish_job_count=await self._count_for_user(session, PublishJob, user.id),
                    )
                )
            return summaries

    async def get_user(self, user_id: uuid.UUID | str) -> User | None:
        parsed_id = self._coerce_uuid(user_id)
        async with get_session_factory()() as session:
            return await session.get(User, parsed_id)

    async def get_user_response(self, user_id: uuid.UUID | str) -> UserResponse | None:
        parsed_id = self._coerce_uuid(user_id)
        async with get_session_factory()() as session:
            user = await session.get(User, parsed_id)
            if user is None:
                return None
            return UserResponse(**self._user_payload(user))

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

    # async def save_generated_content(
    #     self,
    #     raw_output: dict[str, Any],
    #     video_script: dict[str, Any] | list[Any],
    #     platform_posts: dict[str, Any],
    #     thumbnail: dict[str, Any] | None,
    #     user_id: uuid.UUID | str | None = None,
    #     trend_analysis_id: uuid.UUID | str | None = None,
    #     selected_keyword: str | None = None,
    #     main_title: str | None = None,
    #     music_background: str | None = None,
    #     status: str = "generated",
    # ) -> GeneratedContent:
    #     async with get_session_factory()() as session:
    #         content = GeneratedContent(
    #             user_id=self._coerce_uuid(user_id) if user_id else None,
    #             trend_analysis_id=self._coerce_uuid(trend_analysis_id) if trend_analysis_id else None,
    #             selected_keyword=selected_keyword,
    #             main_title=main_title,
    #             video_script=video_script,
    #             platform_posts=platform_posts,
    #             thumbnail=thumbnail,
    #             music_background=music_background,
    #             raw_output=raw_output,
    #             status=status,
    #         )
    #         session.add(content)
    #         await session.commit()
    #         await session.refresh(content)
    #         return content

    # async def list_generated_contents(
    #     self,
    #     user_id: uuid.UUID | str | None = None,
    #     limit: int = 20,
    # ) -> list[GeneratedContent]:
    #     async with get_session_factory()() as session:
    #         statement = select(GeneratedContent).order_by(GeneratedContent.created_at.desc()).limit(limit)
    #         if user_id:
    #             statement = statement.where(GeneratedContent.user_id == self._coerce_uuid(user_id))
    #         result = await session.execute(statement)
    #         return list(result.scalars().all())
    async def save_generated_content(
        self,
        raw_output: dict[str, Any],
        video_script: dict[str, Any],
        platform_posts: dict[str, Any],
        user_id: uuid.UUID | str | None = None,
        trend_analysis_id: uuid.UUID | str | None = None,
        selected_keyword: str | None = None,
        main_title: str | None = None,
        music_background: str | None = None,
        status: str = "generated",
    ) -> GeneratedContent:
        """
        Persist a GeneratedContent record.
 
        Per the Generating_agent.json schema:
        - ``video_script`` is the full object including ``sections``, each of
          which carries its own ``thumbnail`` dict (prompt, style, size,
          output_path).  There is no separate top-level thumbnail argument.
        - ``platform_posts`` holds per-platform dicts (tiktok / facebook /
          instagram) with caption, hashtags, cta, best_post_time, and
          thumbnail_description.
        - ``music_background`` is the top-level music description string.
        """
        async with get_session_factory()() as session:
            content = GeneratedContent(
                user_id=self._coerce_uuid(user_id) if user_id else None,
                trend_analysis_id=self._coerce_uuid(trend_analysis_id) if trend_analysis_id else None,
                selected_keyword=selected_keyword,
                main_title=main_title,
                video_script=video_script,
                platform_posts=platform_posts,
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

    async def get_generated_content(self, content_id: uuid.UUID | str) -> GeneratedContent | None:
        parsed_id = self._coerce_uuid(content_id)
        async with get_session_factory()() as session:
            return await session.get(GeneratedContent, parsed_id)

    async def save_publish_job(
        self,
        profile_username: str,
        platforms: list[str],
        title: str,
        provider_response: dict[str, Any],
        user_id: uuid.UUID | str | None = None,
        generated_content_id: uuid.UUID | str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        first_comment: str | None = None,
        schedule_post: str | None = None,
        link_url: str | None = None,
        subreddit: str | None = None,
        asset_urls: list[str] | None = None,
        uploaded_files: list[dict[str, Any]] | None = None,
        post_kind: str = "text",
        status: str = "submitted",
    ) -> PublishJob:
        payload = provider_response.get("payload", {}) if isinstance(provider_response, dict) else {}
        provider_request_id = self._coerce_optional_str(payload.get("request_id") or provider_response.get("request_id"))
        provider_job_id = self._coerce_optional_str(payload.get("job_id") or provider_response.get("job_id"))

        async with get_session_factory()() as session:
            publish_job = PublishJob(
                user_id=self._coerce_uuid(user_id) if user_id else None,
                generated_content_id=self._coerce_uuid(generated_content_id) if generated_content_id else None,
                profile_username=profile_username,
                platforms=platforms,
                title=title,
                description=description,
                tags=tags or [],
                first_comment=first_comment,
                schedule_post=schedule_post,
                link_url=link_url,
                subreddit=subreddit,
                asset_urls=asset_urls or [],
                uploaded_files=uploaded_files or [],
                post_kind=post_kind,
                provider_request_id=provider_request_id,
                provider_job_id=provider_job_id,
                provider_response=provider_response,
                status=status,
            )
            session.add(publish_job)
            await session.commit()
            await session.refresh(publish_job)
            return publish_job

    async def list_publish_jobs(
        self,
        user_id: uuid.UUID | str | None = None,
        generated_content_id: uuid.UUID | str | None = None,
        limit: int = 20,
    ) -> list[PublishJob]:
        async with get_session_factory()() as session:
            statement = select(PublishJob).order_by(PublishJob.created_at.desc()).limit(limit)
            if user_id:
                statement = statement.where(PublishJob.user_id == self._coerce_uuid(user_id))
            if generated_content_id:
                statement = statement.where(PublishJob.generated_content_id == self._coerce_uuid(generated_content_id))
            result = await session.execute(statement)
            return list(result.scalars().all())

    async def get_publish_job(self, publish_job_id: uuid.UUID | str) -> PublishJob | None:
        parsed_id = self._coerce_uuid(publish_job_id)
        async with get_session_factory()() as session:
            return await session.get(PublishJob, parsed_id)

    def _coerce_uuid(self, value: uuid.UUID | str) -> uuid.UUID:
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))

    def _coerce_optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    async def _count_for_user(self, session, model, user_id: uuid.UUID) -> int:
        result = await session.execute(select(func.count()).where(model.user_id == user_id))
        return int(result.scalar_one() or 0)

    def _user_payload(self, user: User) -> dict[str, Any]:
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "plan": user.plan,
            "upload_post_account": user.upload_post_account or {},
            "profiles": user.profiles or [],
            "social_accounts": user.social_accounts or {},
            "connected_platforms": user.connected_platforms or [],
            "created_at": user.created_at,
        }
