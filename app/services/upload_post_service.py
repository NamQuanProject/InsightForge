import json
import os
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
    def __init__(self) -> None:
        load_dotenv()
        self.base_url = os.getenv("UPLOAD_POST_BASE_URL", "https://api.upload-post.com/api").rstrip("/")
        self.timeout = float(os.getenv("UPLOAD_POST_TIMEOUT_SECONDS", "30"))

    def get_current_user(self) -> dict[str, Any]:
        return self._request_json("GET", "/uploadposts/me", headers=self._api_key_headers())

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
        data = self._request_with_token_fallback(
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
        jwt_token: str,
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

        return self._request_with_token_fallback(
            "GET",
            f"/analytics/{profile_username}",
            jwt_token=jwt_token,
            query=query,
            schemes=("Apikey", "Bearer"),
        )

    def get_total_impressions(
        self,
        profile_username: str,
        jwt_token: str,
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

        return self._request_with_token_fallback(
            "GET",
            f"/uploadposts/total-impressions/{profile_username}",
            jwt_token=jwt_token,
            query=query,
            schemes=("Apikey", "Bearer"),
        )

    def get_post_analytics(self, request_id: str, jwt_token: str, platform: str | None = None) -> dict[str, Any]:
        query = {"platform": platform} if platform else None
        return self._request_with_token_fallback(
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

    def _request_with_token_fallback(
        self,
        method: str,
        path: str,
        jwt_token: str,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        schemes: tuple[str, ...] = ("Apikey", "Bearer"),
    ) -> dict[str, Any]:
        token = self._resolve_jwt(jwt_token)
        last_error: HTTPException | None = None
        for scheme in schemes:
            try:
                return self._request_json(
                    method,
                    path,
                    query=query,
                    body=body,
                    headers={"Authorization": f"{scheme} {token}"},
                )
            except HTTPException as exc:
                last_error = exc
                if exc.status_code != 401 or scheme == schemes[-1]:
                    raise
        if last_error is not None:
            raise last_error
        raise HTTPException(status_code=500, detail="Upload-Post request failed unexpectedly.")

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

    def _normalize_profile(self, payload: dict[str, Any] | None) -> UploadPostProfile:
        if payload is None:
            raise HTTPException(status_code=502, detail="Upload-Post returned an empty profile payload.")

        social_accounts = payload.get("social_accounts") or payload.get("socials") or {}
        if not isinstance(social_accounts, dict):
            social_accounts = {"raw": social_accounts}

        return UploadPostProfile(
            username=str(payload.get("username") or payload.get("user") or ""),
            created_at=payload.get("created_at"),
            social_accounts=social_accounts,
        )

    def _coerce_int(self, value: Any) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
