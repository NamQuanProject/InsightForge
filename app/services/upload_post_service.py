import json
import os
import re
import unicodedata
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from fastapi import HTTPException

from app.schema.upload_post import (
    UploadPostCreateProfileRequest,
    UploadPostGenerateJwtRequest,
    UploadPostProfile,
)


class UploadPostApiService:
    VIETNAMESE_BAD_WORDS = (
        "địt",
        "đụ",
        "đéo",
        "đĩ",
        "đĩ mẹ",
        "lồn",
        "cặc",
        "buồi",
        "vãi lồn",
        "vãi",
        "mẹ mày",
        "con mẹ mày",
        "bố mày",
        "óc chó",
        "chó má",
        "đồ chó",
        "ngu",
        "ngu xuẩn",
        "đồ ngu",
        "khốn nạn",
        "cút",
        "cút mẹ",
        "chết mẹ",
        "mất dạy",
        "súc vật",
    )
    PROFILE_USER_ENV_KEYS = (
        "UPLOAD_POST_DEFAULT_USER",
        "UPLOAD_POST_YOUTUBE_USER",
        "UPLOAD_POST_TIKTOK_USER",
        "UPLOAD_POST_INSTAGRAM_USER",
        "UPLOAD_POST_FACEBOOK_USER",
        "UPLOAD_POST_X_USER",
        "UPLOAD_POST_THREADS_USER",
        "UPLOAD_POST_LINKEDIN_USER",
        "UPLOAD_POST_BLUESKY_USER",
        "UPLOAD_POST_REDDIT_USER",
        "UPLOAD_POST_PINTEREST_USER",
        "UPLOAD_POST_GOOGLE_BUSINESS_USER",
    )

    def __init__(self) -> None:
        load_dotenv()
        self.base_url = os.getenv("UPLOAD_POST_BASE_URL", "https://api.upload-post.com/api").rstrip("/")
        self.timeout = float(os.getenv("UPLOAD_POST_TIMEOUT_SECONDS", "30"))

    def get_current_user(self) -> dict[str, Any]:
        return self._request_json("GET", "/uploadposts/me", headers=self._api_key_headers())

    def get_account_bundle(self) -> dict[str, Any]:
        account = self.get_current_user()
        profiles_payload = self._request_json("GET", "/uploadposts/users", headers=self._api_key_headers())
        raw_profiles = profiles_payload.get("profiles", [])
        if not isinstance(raw_profiles, list):
            raw_profiles = []

        profiles = [self._profile_dict(item) for item in raw_profiles if isinstance(item, dict)]
        social_accounts = self._collect_social_accounts(profiles)
        connected_platforms = sorted(social_accounts.keys())

        return {
            "account": account,
            "profiles_payload": profiles_payload,
            "profiles": profiles,
            "social_accounts": social_accounts,
            "connected_platforms": connected_platforms,
        }

    def get_configured_profile_username(self) -> str | None:
        for key in self.PROFILE_USER_ENV_KEYS:
            value = os.getenv(key)
            if value and value.strip():
                return value.strip()
        return None

    def create_profile(self, payload: UploadPostCreateProfileRequest) -> dict[str, Any]:
        data = self._request_json(
            "POST",
            "/uploadposts/users",
            headers=self._api_key_headers(),
            body={"username": payload.username},
        )
        return {
            "success": bool(data.get("success", True)),
            "profile": self._normalize_profile(data),
        }

    def get_profiles(self) -> dict[str, Any]:
        data = self._request_json("GET", "/uploadposts/users", headers=self._api_key_headers())
        profiles = [self._normalize_profile(item) for item in data.get("profiles", [])]
        return {
            "success": bool(data.get("success", True)),
            "plan": data.get("plan"),
            "limit": self._coerce_int(data.get("limit")),
            "profiles": profiles,
        }

    def get_profile(self, username: str) -> dict[str, Any]:
        profiles = self.get_profiles()["profiles"]
        profile = next((item for item in profiles if item.username == username), None)
        if profile is None:
            raise HTTPException(status_code=404, detail=f"Upload-Post profile not found: {username}")
        return {"success": True, "profile": profile}

    def delete_profile(self, username: str) -> dict[str, Any]:
        data = self._request_json(
            "DELETE",
            "/uploadposts/users",
            headers=self._api_key_headers(),
            body={"username": username},
        )
        return {
            "success": bool(data.get("success", True)),
            "message": data.get("message") or f"Deleted profile {username}",
        }

    def generate_jwt(self, payload: UploadPostGenerateJwtRequest) -> dict[str, Any]:
        body: dict[str, Any] = {"username": payload.username}
        optional_fields = {
            "redirect_url": payload.redirect_url,
            "logo_image": payload.logo_image,
            "redirect_button_text": payload.redirect_button_text,
            "connect_title": payload.connect_title,
            "connect_description": payload.connect_description,
            "show_calendar": payload.show_calendar,
            "readonly_calendar": payload.readonly_calendar,
        }
        body.update({key: value for key, value in optional_fields.items() if value is not None})
        if payload.platforms:
            body["platforms"] = payload.platforms

        data = self._request_json(
            "POST",
            "/uploadposts/users/generate-jwt",
            headers=self._api_key_headers(),
            body=body,
        )
        return {
            "success": bool(data.get("success", True)),
            "access_url": data.get("access_url") or data.get("url") or "",
            "duration": data.get("duration"),
        }

    def validate_jwt(self, jwt_token: str) -> dict[str, Any]:
        data = self._request_with_auth_fallback(
            "POST",
            "/uploadposts/users/validate-jwt",
            jwt_token=jwt_token,
            body=None,
            schemes=("Bearer",),
        )
        profile_data = data.get("profile")
        return {
            "success": data.get("success"),
            "isValid": data.get("isValid"),
            "reason": data.get("reason"),
            "profile": self._normalize_profile(profile_data) if isinstance(profile_data, dict) else None,
        }

    def get_profile_analytics(
        self,
        profile_username: str,
        platforms: list[str],
        jwt_token: str | None = None,
        page_id: str | None = None,
        page_urn: str | None = None,
    ) -> dict[str, Any]:
        if not platforms:
            raise HTTPException(status_code=400, detail="At least one platform is required.")

        query = {"platforms": ",".join(platforms)}
        if page_id:
            query["page_id"] = page_id
        if page_urn:
            query["page_urn"] = page_urn

        return self._request_with_auth_fallback(
            "GET",
            f"/analytics/{profile_username}",
            jwt_token=jwt_token,
            query=query,
            schemes=("Apikey", "Bearer"),
        )

    def get_total_impressions(
        self,
        profile_username: str,
        jwt_token: str | None = None,
        date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        period: str | None = None,
        platform: list[str] | None = None,
        breakdown: bool = False,
        metrics: list[str] | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {}
        if date:
            query["date"] = date
        if start_date:
            query["start_date"] = start_date
        if end_date:
            query["end_date"] = end_date
        if period:
            query["period"] = period
        if platform:
            query["platform"] = ",".join(platform)
        if breakdown:
            query["breakdown"] = "true"
        if metrics:
            query["metrics"] = ",".join(metrics)

        return self._request_with_auth_fallback(
            "GET",
            f"/uploadposts/total-impressions/{profile_username}",
            jwt_token=jwt_token,
            query=query,
            schemes=("Apikey", "Bearer"),
        )

    def get_post_analytics(
        self,
        request_id: str,
        jwt_token: str | None = None,
        platform: str | None = None,
    ) -> dict[str, Any]:
        query = {"platform": platform} if platform else None
        return self._request_with_auth_fallback(
            "GET",
            f"/uploadposts/post-analytics/{request_id}",
            jwt_token=jwt_token,
            query=query,
            schemes=("Apikey", "Bearer"),
        )

    def get_history(
        self,
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        query = {
            "page": str(page),
            "limit": str(limit),
        }
        return self._request_json(
            "GET",
            "/uploadposts/history",
            headers=self._api_key_headers(),
            query=query,
        )

    def get_media(
        self,
        platform: str,
        user: str,
    ) -> dict[str, Any]:
        return self._request_json(
            "GET",
            "/uploadposts/media",
            headers=self._api_key_headers(),
            query={"platform": platform, "user": user},
        )

    def get_comments(
        self,
        platform: str,
        user: str,
        post_id: str | None = None,
        post_url: str | None = None,
    ) -> dict[str, Any]:
        if not post_id and not post_url:
            raise HTTPException(status_code=400, detail="Provide either post_id or post_url.")

        query: dict[str, Any] = {}
        query["platform"] = platform
        query["user"] = user
        if post_id:
            query["post_id"] = post_id
        if post_url:
            query["post_url"] = post_url

        return self._request_json(
            "GET",
            "/uploadposts/comments",
            headers=self._api_key_headers(),
            query=query,
        )

    def get_all_comments(
        self,
        platform: str,
        user: str,
        max_media: int = 20,
        continue_on_error: bool = True,
    ) -> dict[str, Any]:
        media_payload = self.get_media(platform=platform, user=user)
        media_items = self._extract_media_items(media_payload)[:max_media]
        media_comments: list[dict[str, Any]] = []
        total_comments = 0

        for media in media_items:
            post_id = self._coerce_optional_str(media.get("id") or media.get("post_id") or media.get("media_id"))
            post_url = self._coerce_optional_str(media.get("permalink") or media.get("url") or media.get("post_url"))

            if not post_id and not post_url:
                media_comments.append(
                    {
                        "media": media,
                        "success": False,
                        "comments": [],
                        "error": "Media item does not include an id or permalink usable by Upload-Post comments.",
                    }
                )
                continue

            try:
                comments_payload = self.get_comments(
                    platform=platform,
                    user=user,
                    post_id=post_id,
                    post_url=post_url if not post_id else None,
                )
            except HTTPException as exc:
                if not continue_on_error:
                    raise
                media_comments.append(
                    {
                        "media": media,
                        "post_id": post_id,
                        "post_url": post_url,
                        "success": False,
                        "comments": [],
                        "error": exc.detail,
                    }
                )
                continue

            comments = self._extract_comments(comments_payload)
            total_comments += len(comments)
            media_comments.append(
                {
                    "media": media,
                    "post_id": post_id,
                    "post_url": post_url,
                    "success": bool(comments_payload.get("success", True)),
                    "comments": comments,
                    "payload": comments_payload,
                }
            )

        return {
            "success": True,
            "platform": platform,
            "user": user,
            "media_count": len(media_items),
            "total_comments": total_comments,
            "media_payload": media_payload,
            "media_comments": media_comments,
        }

    def delete_bad_word_comments(
        self,
        platform: str,
        user: str,
        post_id: str | None = None,
        post_url: str | None = None,
        max_media: int = 20,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        payload = (
            {
                "success": True,
                "platform": platform,
                "user": user,
                "media_comments": [
                    {
                        "post_id": post_id,
                        "post_url": post_url,
                        "comments": self._extract_comments(
                            self.get_comments(
                                platform=platform,
                                user=user,
                                post_id=post_id,
                                post_url=post_url,
                            )
                        ),
                    }
                ],
            }
            if post_id or post_url
            else self.get_all_comments(platform=platform, user=user, max_media=max_media)
        )

        matches: list[dict[str, Any]] = []
        for media_group in payload.get("media_comments", []):
            if not isinstance(media_group, dict):
                continue
            for comment in media_group.get("comments", []):
                if not isinstance(comment, dict):
                    continue
                text = self._comment_text(comment)
                matched_words = self.find_vietnamese_bad_words(text)
                if not matched_words:
                    continue

                comment_id = self._coerce_optional_str(comment.get("id") or comment.get("comment_id"))
                result: dict[str, Any] = {
                    "deleted": False,
                    "skipped": dry_run,
                    "provider_payload": None,
                    "error": None,
                }
                if comment_id and not dry_run:
                    try:
                        result["provider_payload"] = self.delete_comment(
                            platform=platform,
                            user=user,
                            comment_id=comment_id,
                            post_id=self._coerce_optional_str(media_group.get("post_id")) or post_id,
                            post_url=self._coerce_optional_str(media_group.get("post_url")) or post_url,
                        )
                        result["deleted"] = bool(result["provider_payload"].get("success", True))
                    except HTTPException as exc:
                        result["error"] = exc.detail
                elif not comment_id:
                    result["error"] = "Comment does not include an id/comment_id."

                matches.append(
                    {
                        "post_id": media_group.get("post_id") or post_id,
                        "post_url": media_group.get("post_url") or post_url,
                        "comment_id": comment_id,
                        "text": text,
                        "matched_bad_words": matched_words,
                        "comment": comment,
                        **result,
                    }
                )

        deleted_count = sum(1 for item in matches if item["deleted"])
        failed_count = sum(1 for item in matches if item["error"] and not item["skipped"])

        return {
            "success": failed_count == 0,
            "platform": platform,
            "user": user,
            "dry_run": dry_run,
            "bad_words": list(self.VIETNAMESE_BAD_WORDS),
            "scanned_media_count": len(payload.get("media_comments", [])),
            "matched_count": len(matches),
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "matches": matches,
            "comments_payload": payload,
        }

    def delete_comment(
        self,
        platform: str,
        user: str,
        comment_id: str,
        post_id: str | None = None,
        post_url: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "platform": platform,
            "user": user,
            "comment_id": comment_id,
        }
        if post_id:
            body["post_id"] = post_id
        if post_url:
            body["post_url"] = post_url

        return self._request_json(
            "DELETE",
            "/uploadposts/comments",
            headers=self._api_key_headers(),
            body=body,
        )

    def find_vietnamese_bad_words(self, text: str) -> list[str]:
        normalized_text = f" {self._normalize_vietnamese_text(text)} "
        matches: list[str] = []
        for word in self.VIETNAMESE_BAD_WORDS:
            normalized_word = self._normalize_vietnamese_text(word)
            if normalized_word and f" {normalized_word} " in normalized_text:
                matches.append(word)
        return matches

    def _api_key_headers(self) -> dict[str, str]:
        api_key = os.getenv("UPLOAD_POST_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing UPLOAD_POST_API_KEY in the backend environment.")
        return {"Authorization": f"Apikey {api_key}"}

    def _resolve_jwt(self, jwt_token: str | None) -> str:
        token = jwt_token or os.getenv("UPLOAD_POST_JWT")
        if not token:
            raise HTTPException(
                status_code=400,
                detail="Missing Upload-Post JWT. Pass it in the request or set UPLOAD_POST_JWT.",
            )
        return token

    def _request_with_auth_fallback(
        self,
        method: str,
        path: str,
        jwt_token: str | None = None,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        schemes: tuple[str, ...] = ("Apikey", "Bearer"),
    ) -> dict[str, Any]:
        auth_headers = self._build_auth_headers(jwt_token=jwt_token, schemes=schemes)
        last_error: HTTPException | None = None
        for headers in auth_headers:
            try:
                return self._request_json(
                    method,
                    path,
                    query=query,
                    body=body,
                    headers=headers,
                )
            except HTTPException as exc:
                last_error = exc
                if exc.status_code != 401 or headers == auth_headers[-1]:
                    raise
        if last_error is not None:
            raise last_error
        raise HTTPException(status_code=500, detail="Upload-Post request failed unexpectedly.")

    def _build_auth_headers(
        self,
        jwt_token: str | None,
        schemes: tuple[str, ...],
    ) -> list[dict[str, str]]:
        auth_headers: list[dict[str, str]] = []
        for scheme in schemes:
            if scheme == "Apikey":
                api_key = os.getenv("UPLOAD_POST_API_KEY")
                if api_key:
                    auth_headers.append({"Authorization": f"Apikey {api_key}"})
            elif scheme == "Bearer":
                token = jwt_token or os.getenv("UPLOAD_POST_JWT")
                if token:
                    auth_headers.append({"Authorization": f"Bearer {token}"})
            else:
                raise HTTPException(status_code=500, detail=f"Unsupported Upload-Post auth scheme: {scheme}")

        if auth_headers:
            return auth_headers

        if schemes == ("Bearer",):
            self._resolve_jwt(jwt_token)

        raise HTTPException(status_code=500, detail="Missing UPLOAD_POST_API_KEY in the backend environment.")

    def _request_json(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            query_string = urlencode({key: value for key, value in query.items() if value is not None})
            if query_string:
                url = f"{url}?{query_string}"

        request_headers = {"Accept": "application/json", **headers}
        data: bytes | None = None
        if body is not None:
            request_headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")

        request = Request(url=url, data=data, headers=request_headers, method=method.upper())

        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raise self._provider_error(exc) from exc
        except URLError as exc:
            raise HTTPException(status_code=502, detail=f"Upload-Post connection failed: {exc.reason}") from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Unexpected Upload-Post failure: {exc}") from exc

        if not raw:
            return {"success": True}

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"success": True, "raw": raw}

    def _provider_error(self, exc: HTTPError) -> HTTPException:
        raw = exc.read().decode("utf-8", errors="replace")
        detail: Any = raw or exc.reason
        try:
            payload = json.loads(raw)
            detail = payload
        except json.JSONDecodeError:
            pass
        return HTTPException(status_code=exc.code, detail=detail)

    def _extract_media_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("media", "items", "data", "posts", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []

    def _extract_comments(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("comments", "items", "data", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []

    def _comment_text(self, comment: dict[str, Any]) -> str:
        for key in ("text", "message", "comment", "body", "content"):
            value = comment.get(key)
            if value is not None:
                return str(value)
        return ""

    def _normalize_vietnamese_text(self, value: str) -> str:
        lowered = value.lower().replace("đ", "d")
        decomposed = unicodedata.normalize("NFD", lowered)
        without_marks = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
        return re.sub(r"[^a-z0-9]+", " ", without_marks).strip()

    def _normalize_profile(self, payload: dict[str, Any] | None) -> UploadPostProfile:
        if payload is None:
            raise HTTPException(status_code=502, detail="Upload-Post returned an empty profile payload.")

        social_accounts = self._extract_social_accounts(payload)
        if not isinstance(social_accounts, dict):
            social_accounts = {"raw": social_accounts}

        return UploadPostProfile(
            username=str(payload.get("username") or payload.get("user") or ""),
            created_at=payload.get("created_at"),
            social_accounts=social_accounts,
        )

    def _profile_dict(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_profile(payload)
        profile = normalized.model_dump()
        profile["raw"] = payload
        return profile

    def _extract_social_accounts(self, payload: dict[str, Any]) -> dict[str, Any]:
        for key in ("social_accounts", "socials", "connected_accounts", "accounts", "platforms"):
            value = payload.get(key)
            if isinstance(value, dict):
                return value
            if isinstance(value, list):
                return self._social_account_list_to_dict(value)
        return {}

    def _social_account_list_to_dict(self, values: list[Any]) -> dict[str, Any]:
        accounts: dict[str, Any] = {}
        for index, value in enumerate(values):
            if isinstance(value, dict):
                platform = (
                    value.get("platform")
                    or value.get("provider")
                    or value.get("type")
                    or value.get("name")
                    or f"account_{index + 1}"
                )
                accounts[str(platform)] = value
            else:
                accounts[str(value)] = {"value": value}
        return accounts

    def _collect_social_accounts(self, profiles: list[dict[str, Any]]) -> dict[str, Any]:
        social_accounts: dict[str, Any] = {}
        for profile in profiles:
            username = str(profile.get("username") or "")
            accounts = profile.get("social_accounts")
            if not isinstance(accounts, dict):
                continue
            for platform, account in accounts.items():
                platform_key = str(platform)
                social_accounts.setdefault(platform_key, [])
                social_accounts[platform_key].append(
                    {
                        "profile_username": username,
                        "account": account,
                    }
                )
        return social_accounts

    def _coerce_int(self, value: Any) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _coerce_optional_str(self, value: Any) -> str | None:
        if value is None or value == "":
            return None
        return str(value)
