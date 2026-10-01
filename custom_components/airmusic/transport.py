"""Serialized communication with embedded AirMusic HTTP servers."""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

import aiohttp

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
REQUEST_INTERVAL = 1.0
REQUEST_TIMEOUT = 10


@dataclass
class RequestGate:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    next_request: float = 0.0


def host_gate(hass, host: str) -> RequestGate:
    """Share the gate across all entries and ports of the same radio."""
    gates = hass.data.setdefault(DOMAIN, {}).setdefault("request_gates", {})
    return gates.setdefault(host.lower(), RequestGate())


class RadioTransport:
    """A dedicated session with no persistent TCP connections."""

    def __init__(self, hass, host: str, auth: aiohttp.BasicAuth):
        self.host = host
        self.auth = auth
        self.gate = host_gate(hass, host)
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(force_close=True, limit_per_host=1),
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
        )

    async def close(self):
        await self.session.close()

    async def serialized(self, operation):
        """Wait at least one second after completion, including failed calls.

        The monotonic deadline survives cancellation and session replacement.
        It is shared between API, SOAP, artwork and UPnP control operations.
        """
        async with self.gate.lock:
            loop = asyncio.get_running_loop()
            await asyncio.sleep(max(0.0, self.gate.next_request - loop.time()))
            try:
                return await operation()
            finally:
                self.gate.next_request = loop.time() + REQUEST_INTERVAL

    async def request(self, method: str, url: str, *, binary=False,
                      authenticate=True, **kwargs) -> Any:
        async def operation():
            try:
                async with self.session.request(
                    method, url, auth=self.auth if authenticate else None, **kwargs
                ) as response:
                    response.raise_for_status()
                    if binary:
                        return await response.read(), response.content_type
                    return await response.text()
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                # Do not put stream query strings / signed tokens in logs.
                _LOGGER.debug("AirMusic request failed (%s %s): %s", method,
                              urlsplit(url).path, type(err).__name__)
                return None

        return await self.serialized(operation)
