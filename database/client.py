import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Any, Dict, List

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")


class SupabaseService:
    def __init__(self):
        self.supabase: Client | None = None
        if url and key:
            self.supabase = create_client(
                supabase_url=url,
                supabase_key=key,
            )

    @property
    def is_configured(self) -> bool:
        return self.supabase is not None

    def _require_client(self) -> Client:
        if self.supabase is None:
            raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY.")
        return self.supabase

    # -------------------------
    # GET (READ)
    # -------------------------
    def get_all(self, table: str) -> List[Dict[str, Any]]:
        response = self._require_client().table(table).select("*").execute()
        return response.data

    def get_by_id(self, table: str, column: str, value: Any) -> Dict[str, Any]:
        response = (
            self._require_client()
            .table(table)
            .select("*")
            .eq(column, value)
            .single()
            .execute()
        )
        return response.data

    def filter(self, table: str, column: str, value: Any) -> List[Dict[str, Any]]:
        response = (
            self._require_client()
            .table(table)
            .select("*")
            .eq(column, value)
            .execute()
        )
        return response.data

    # -------------------------
    # INSERT (POST)
    # -------------------------
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self._require_client().table(table).insert(data).execute()
        return response.data

    def bulk_insert(self, table: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        response = self._require_client().table(table).insert(data).execute()
        return response.data

    # -------------------------
    # UPDATE
    # -------------------------
    def update(self, table: str, column: str, value: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        response = (
            self._require_client()
            .table(table)
            .update(data)
            .eq(column, value)
            .execute()
        )
        return response.data

    # -------------------------
    # DELETE
    # -------------------------
    def delete(self, table: str, column: str, value: Any) -> Dict[str, Any]:
        response = (
            self._require_client()
            .table(table)
            .delete()
            .eq(column, value)
            .execute()
        )
        return response.data
    




db = SupabaseService()
