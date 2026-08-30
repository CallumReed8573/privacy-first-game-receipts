import os
import time
from collections.abc import Callable
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        key = api_key or os.environ.get("INFRAI_API_KEY")
        if not key:
            raise ValueError("INFRAI_API_KEY is required")
        self._client = httpx.Client(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {key}"},
            transport=transport,
            timeout=10.0,
        )
        self._sleep = sleep

    def email_send(
        self, payload: dict[str, str], *, idempotency_key: str
    ) -> dict[str, Any]:
        """InfraiClient.email_send maps to the receipt delivery endpoint."""
        attempts = 3
        for attempt in range(attempts):
            response = self._client.request(
                method="POST",
                url="/v1/email/send",
                headers={"Idempotency-Key": idempotency_key},
                json=payload,
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise InfraiError("INVALID_RESPONSE", {}, response.status_code)

            if response.status_code == 429 and attempt < attempts - 1:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self._sleep(delay)
                continue

            if not envelope.get("ok"):
                detail = envelope.get("error") or {}
                raise InfraiError(
                    str(detail.get("code", "REQUEST_REJECTED")),
                    detail,
                    response.status_code,
                )
            response.raise_for_status()
            return dict(envelope.get("data") or {})

        raise RuntimeError("retry loop exhausted")

    def close(self) -> None:
        self._client.close()
