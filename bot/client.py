from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from bot.exceptions import APIError, NetworkError


class BinanceFuturesClient:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://testnet.binancefuture.com",
        timeout: float = 10.0,
        max_retries: int = 2,
        logger: Any | None = None,
    ):
        self.api_key = api_key
        self.api_secret = api_secret.encode("utf-8")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logger
        self._http = httpx.Client(timeout=self.timeout)

    def close(self) -> None:
        self._http.close()

    def _sign(self, params: dict[str, Any]) -> str:
        query = urlencode(params, doseq=True)
        return hmac.new(self.api_secret, query.encode("utf-8"), hashlib.sha256).hexdigest()

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        signed: bool = False,
    ) -> dict[str, Any]:
        payload = dict(params or {})
        headers = {"X-MBX-APIKEY": self.api_key}

        if signed:
            payload["timestamp"] = int(time.time() * 1000)
            payload["recvWindow"] = 5000
            payload["signature"] = self._sign(payload)

        url = f"{self.base_url}{path}"
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                if self.logger:
                    safe_payload = dict(payload)
                    if "signature" in safe_payload:
                        safe_payload["signature"] = "***"
                    self.logger.info(
                        "api_request method=%s path=%s params=%s",
                        method.upper(),
                        path,
                        json.dumps(safe_payload, default=str),
                    )

                response = self._http.request(
                    method=method,
                    url=url,
                    params=payload if method.upper() in {"GET", "DELETE"} else None,
                    data=payload if method.upper() in {"POST", "PUT"} else None,
                    headers=headers,
                )

                if self.logger:
                    self.logger.info(
                        "api_response status=%s body=%s",
                        response.status_code,
                        response.text,
                    )

                try:
                    body = response.json()
                except ValueError:
                    body = {"message": response.text}

                if response.status_code >= 400:
                    raise APIError(
                        message=body.get("msg", "Binance API returned an error."),
                        status_code=response.status_code,
                        code=body.get("code"),
                    )

                if not isinstance(body, dict):
                    raise APIError("Unexpected API response format.")
                return body

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    if self.logger:
                        self.logger.error("network_error %s", str(exc))
                    raise NetworkError(f"Network error while calling Binance API: {exc}") from exc
                time.sleep(0.3 * (attempt + 1))
            except APIError as exc:
                if self.logger:
                    self.logger.error(
                        "api_error status=%s code=%s message=%s",
                        getattr(exc, "status_code", None),
                        getattr(exc, "code", None),
                        str(exc),
                    )
                raise

        raise NetworkError(f"Network error while calling Binance API: {last_error}")

    def place_order(self, params: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

