from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx


HTTP_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    412: "FAILED_PRECONDITION",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    503: "PROVIDER_UNAVAILABLE",
}


class MnemeRestClient:
    def __init__(
        self,
        *,
        base_url: str,
        token: str | None = None,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.transport = transport

    def _headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    async def post_tool(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", f"/v1/tools/{quote(name, safe='')}", json=payload)

    async def cost_report(self, session_id: str) -> dict[str, Any]:
        session = quote(session_id, safe="")
        return await self._request("GET", f"/v1/costs/session/{session}")

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._headers(),
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = await client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            return self._error_envelope(
                {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": str(exc),
                    "retryable": True,
                    "details": {"base_url": self.base_url},
                }
            )

        if response.status_code >= 400:
            return self._error_envelope(self._response_error(response))

        body = self._response_json(response)
        if isinstance(body, dict) and "ok" in body:
            envelope = dict(body)
            envelope.setdefault("warnings", [])
            return envelope
        return {"ok": True, "data": body, "warnings": []}

    def _response_error(self, response: httpx.Response) -> dict[str, Any]:
        body = self._response_json(response)
        if isinstance(body, dict) and isinstance(body.get("error"), dict):
            error = dict(body["error"])
        else:
            error = {
                "code": HTTP_ERROR_CODES.get(response.status_code, "HTTP_ERROR"),
                "message": self._fallback_error_message(response, body),
                "retryable": response.status_code in {429, 500, 503},
                "details": {"status_code": response.status_code},
            }
        error.setdefault("code", HTTP_ERROR_CODES.get(response.status_code, "HTTP_ERROR"))
        error.setdefault("message", self._fallback_error_message(response, body))
        error.setdefault("retryable", response.status_code in {429, 500, 503})
        error.setdefault("details", {})
        return error

    def _error_envelope(self, error: dict[str, Any]) -> dict[str, Any]:
        return {"ok": False, "error": error, "warnings": []}

    def _response_json(self, response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return None

    def _fallback_error_message(self, response: httpx.Response, body: Any) -> str:
        if isinstance(body, dict) and "detail" in body:
            return str(body["detail"])
        if response.text:
            return response.text
        return f"HTTP {response.status_code}"
