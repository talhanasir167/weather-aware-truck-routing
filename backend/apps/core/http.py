"""Shared httpx helpers.

`trust_env=False` avoids picking up broken HTTP(S)_PROXY values from the
local shell/sandbox that cause ProxyError 403 against public APIs.
"""

from __future__ import annotations

import httpx
from django.conf import settings


def client(**kwargs) -> httpx.Client:
    opts = {
        "timeout": settings.HTTP_TIMEOUT_S,
        "trust_env": False,
    }
    opts.update(kwargs)
    return httpx.Client(**opts)
