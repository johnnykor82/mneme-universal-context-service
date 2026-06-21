from __future__ import annotations

from typing import Any

from fastapi import HTTPException


class MnemeError(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
        trace_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail={
                "ok": False,
                "error": {
                    "code": code,
                    "message": message,
                    "retryable": retryable,
                    "details": details or {},
                    "trace_id": trace_id,
                    "request_id": request_id,
                },
                "warnings": [],
            },
        )


def bad_request(message: str, **details: Any) -> MnemeError:
    return MnemeError(400, "BAD_REQUEST", message, details=details)


def unauthenticated() -> MnemeError:
    return MnemeError(401, "UNAUTHENTICATED", "Missing or invalid authentication.")


def not_found(message: str, **details: Any) -> MnemeError:
    return MnemeError(404, "NOT_FOUND", message, details=details)


def conflict(message: str, **details: Any) -> MnemeError:
    return MnemeError(409, "CONFLICT", message, details=details)


def failed_precondition(message: str, **details: Any) -> MnemeError:
    return MnemeError(412, "FAILED_PRECONDITION", message, details=details)


def payload_too_large(message: str, **details: Any) -> MnemeError:
    return MnemeError(413, "PAYLOAD_TOO_LARGE", message, details=details)


def validation_error(message: str, **details: Any) -> MnemeError:
    return MnemeError(422, "VALIDATION_ERROR", message, details=details)
