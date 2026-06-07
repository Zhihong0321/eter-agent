"""WS handshake auth. Constant-time compare on a shared secret.

For v1 the only auth is a per-deployment shared secret, supplied by the
HoD when they register their phone and baked into the Mac daemon's .env.
JWT-based per-user auth is a future addition.
"""

from __future__ import annotations

import hmac


def authenticate_socket(provided: str, expected: str) -> bool:
    if not provided or not expected:
        return False
    return hmac.compare_digest(provided, expected)
