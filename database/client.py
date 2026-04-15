import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Any, Dict, List

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")


class SupabaseService:
    def __init__(self):
        self.supabase: Client = create_client(
            supabase_url=url,
            supabase_key=key
        )

    # -------------------------
    # GET (READ)
    # -------------------------
    def get_all(self, table: str) -> List[Dict[str, Any]]:
        response = self.supabase.table(table).select("*").execute()
        return response.data

    def get_by_id(self, table: str, column: str, value: Any) -> Dict[str, Any]:
        response = (
            self.supabase
            .table(table)
            .select("*")
            .eq(column, value)
            .single()
            .execute()
        )
        return response.data

    def filter(self, table: str, column: str, value: Any) -> List[Dict[str, Any]]:
        response = (
            self.supabase
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
        response = self.supabase.table(table).insert(data).execute()
        return response.data

    def bulk_insert(self, table: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        response = self.supabase.table(table).insert(data).execute()
        return response.data

    # -------------------------
    # UPDATE
    # -------------------------
    def update(self, table: str, column: str, value: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        response = (
            self.supabase
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
            self.supabase
            .table(table)
            .delete()
            .eq(column, value)
            .execute()
        )
        return response.data
    




db = SupabaseService()

