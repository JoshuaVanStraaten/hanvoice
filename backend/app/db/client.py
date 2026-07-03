"""Thin async client for Supabase PostgREST, using the service-role key.

This is the only place that knows how to talk to PostgREST. Repositories
compose these primitives; routes never touch this class directly. We use a
hand-rolled client instead of ``supabase-py`` for explicit control over
timeouts and headers and so tests can mock plain HTTP with ``respx``.

The service-role key bypasses RLS by design — the schema's security model
(see docs/schema.md) is that this backend is the sole writer of scored,
metered, and billable rows.
"""

from typing import Any

import httpx

from app.core.errors import AppError


class DatabaseError(AppError):
    status_code = 502
    code = "database_error"


JsonRow = dict[str, Any]


class Database:
    def __init__(self, http: httpx.AsyncClient, base_url: str, service_role_key: str):
        self._http = http
        self._rest_url = f"{base_url.rstrip('/')}/rest/v1"
        self._storage_url = f"{base_url.rstrip('/')}/storage/v1"
        self._headers = {
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
        }

    async def select(
        self,
        table: str,
        *,
        columns: str = "*",
        filters: dict[str, str] | None = None,
        order: str | None = None,
        limit: int | None = None,
    ) -> list[JsonRow]:
        """``filters`` values are PostgREST operator expressions, e.g. ``{"id": "eq.7"}``."""
        params: dict[str, str] = {"select": columns, **(filters or {})}
        if order:
            params["order"] = order
        if limit is not None:
            params["limit"] = str(limit)
        response = await self._request("GET", f"/{table}", params=params)
        return self._rows(response)

    async def select_one(
        self,
        table: str,
        *,
        columns: str = "*",
        filters: dict[str, str] | None = None,
    ) -> JsonRow | None:
        rows = await self.select(table, columns=columns, filters=filters, limit=1)
        return rows[0] if rows else None

    async def insert(self, table: str, values: JsonRow | list[JsonRow]) -> list[JsonRow]:
        response = await self._request(
            "POST",
            f"/{table}",
            json=values,
            headers={"Prefer": "return=representation"},
        )
        return self._rows(response)

    async def upsert(
        self, table: str, values: JsonRow, *, on_conflict: str
    ) -> list[JsonRow]:
        response = await self._request(
            "POST",
            f"/{table}",
            params={"on_conflict": on_conflict},
            json=values,
            headers={"Prefer": "return=representation,resolution=merge-duplicates"},
        )
        return self._rows(response)

    async def update(
        self, table: str, values: JsonRow, *, filters: dict[str, str]
    ) -> list[JsonRow]:
        if not filters:
            raise DatabaseError("Refusing to update without filters.")
        response = await self._request(
            "PATCH",
            f"/{table}",
            params=filters,
            json=values,
            headers={"Prefer": "return=representation"},
        )
        return self._rows(response)

    async def rpc(self, function: str, args: JsonRow) -> Any:
        """Call a Postgres function exposed through PostgREST."""
        response = await self._request("POST", f"/rpc/{function}", json=args)
        return response.json() if response.content else None

    async def upload_file(
        self, bucket: str, path: str, content: bytes, content_type: str
    ) -> str:
        """Upload to Supabase Storage; returns the stored object path."""
        url = f"{self._storage_url}/object/{bucket}/{path}"
        try:
            response = await self._http.post(
                url,
                content=content,
                headers={
                    **self._headers,
                    "Content-Type": content_type,
                    "x-upsert": "true",
                },
            )
        except httpx.HTTPError as exc:
            raise DatabaseError(f"Storage request failed: {exc!r}") from exc
        if response.status_code >= 400:
            raise DatabaseError(f"Storage upload failed ({response.status_code}).")
        return f"{bucket}/{path}"

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        try:
            response = await self._http.request(
                method,
                f"{self._rest_url}{path}",
                params=params,
                json=json,
                headers={**self._headers, **(headers or {})},
            )
        except httpx.HTTPError as exc:
            raise DatabaseError(f"Database request failed: {exc!r}") from exc
        if response.status_code >= 400:
            raise DatabaseError(
                f"Database returned {response.status_code} for {method} {path}: "
                f"{response.text[:300]}"
            )
        return response

    @staticmethod
    def _rows(response: httpx.Response) -> list[JsonRow]:
        if not response.content:
            return []
        data = response.json()
        if isinstance(data, list):
            return data
        return [data]
