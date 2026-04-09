import json
import os
from typing import Any

from ..core.config import redis_client

QUEUE_KEY = "jobs:security_events"
EXPIRATION_ZSET_KEY = "jobs:secret_expirations"


def _expiration_member(owner: str, secret_id: int) -> str:
    return f"{owner}:{secret_id}"


def enqueue_security_event(event_type: str, owner: str, site: str, metadata: dict[str, Any] | None = None) -> None:
    # Unit tests should not depend on external Redis availability.
    if os.getenv("PYTEST_CURRENT_TEST"):
        return

    payload = {
        "type": event_type,
        "owner": owner,
        "site": site,
        "metadata": metadata or {},
    }

    try:
        redis_client.rpush(QUEUE_KEY, json.dumps(payload))
    except Exception:
        # Non-blocking behavior: queue errors must not break API requests.
        return


def schedule_secret_expiration(secret_id: int, owner: str, expires_at_epoch: int) -> None:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return

    member = _expiration_member(owner, secret_id)
    try:
        redis_client.zadd(EXPIRATION_ZSET_KEY, {member: expires_at_epoch})
    except Exception:
        return


def clear_secret_expiration(secret_id: int, owner: str) -> None:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return

    member = _expiration_member(owner, secret_id)
    try:
        redis_client.zrem(EXPIRATION_ZSET_KEY, member)
    except Exception:
        return
