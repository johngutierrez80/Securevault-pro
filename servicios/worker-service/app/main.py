# pyright: reportMissingImports=false

import json
import logging
import os
import signal
import time

import redis
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

QUEUE_KEY = os.getenv("WORKER_QUEUE", "jobs:security_events")
EXPIRATION_ZSET_KEY = os.getenv("WORKER_EXPIRATION_ZSET", "jobs:secret_expirations")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vault:vault@postgres:5432/vaultdb")
EXPIRATION_CLEANUP_INTERVAL_SECONDS = int(os.getenv("WORKER_CLEANUP_INTERVAL", "30"))
BLPOP_TIMEOUT_SECONDS = int(os.getenv("WORKER_BLPOP_TIMEOUT", "5"))
REDIS_SOCKET_TIMEOUT_SECONDS = int(os.getenv("WORKER_REDIS_SOCKET_TIMEOUT", "7"))

Base = declarative_base()


class Secret(Base):
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, index=True)


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] worker-service: %(message)s",
)

running = True


def _handle_shutdown(signum, frame):
    del signum, frame
    global running
    logging.info("Shutdown signal received. Stopping worker loop...")
    running = False


def _process_event(raw_payload: str):
    event = json.loads(raw_payload)
    event_type = event.get("type", "unknown")
    owner = event.get("owner", "unknown")
    site = event.get("site", "unknown")

    # Placeholder processing logic for asynchronous tasks.
    logging.info(
        "Processed event type=%s owner=%s site=%s payload=%s",
        event_type,
        owner,
        site,
        event,
    )


def _delete_secret_by_id(owner: str, secret_id: int) -> bool:
    db = SessionLocal()
    try:
        deleted = (
            db.query(Secret)
            .filter(Secret.id == secret_id, Secret.owner == owner)
            .delete(synchronize_session=False)
        )
        db.commit()
        return bool(deleted)
    finally:
        db.close()


def _cleanup_expired_secrets(client: redis.Redis):
    now_epoch = int(time.time())
    members = client.zrangebyscore(EXPIRATION_ZSET_KEY, "-inf", now_epoch)

    if not members:
        return

    for member in members:
        try:
            owner, secret_id_raw = member.split(":", 1)
            secret_id = int(secret_id_raw)
        except Exception:
            client.zrem(EXPIRATION_ZSET_KEY, member)
            logging.warning("Removed malformed expiration member: %s", member)
            continue

        deleted = _delete_secret_by_id(owner, secret_id)
        client.zrem(EXPIRATION_ZSET_KEY, member)

        if deleted:
            logging.info(
                "Expired secret deleted by worker (owner=%s, secret_id=%s)",
                owner,
                secret_id,
            )
        else:
            logging.info(
                "Expired member cleaned with no matching DB row (owner=%s, secret_id=%s)",
                owner,
                secret_id,
            )


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=0,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=REDIS_SOCKET_TIMEOUT_SECONDS,
    )

    logging.info("Worker started. Listening on queue key '%s'", QUEUE_KEY)
    last_cleanup_epoch = 0

    while running:
        try:
            item = client.blpop(QUEUE_KEY, timeout=BLPOP_TIMEOUT_SECONDS)
            if not item:
                if int(time.time()) - last_cleanup_epoch >= EXPIRATION_CLEANUP_INTERVAL_SECONDS:
                    _cleanup_expired_secrets(client)
                    last_cleanup_epoch = int(time.time())
                continue

            _, payload = item
            _process_event(payload)

            if int(time.time()) - last_cleanup_epoch >= EXPIRATION_CLEANUP_INTERVAL_SECONDS:
                _cleanup_expired_secrets(client)
                last_cleanup_epoch = int(time.time())
        except json.JSONDecodeError as exc:
            logging.warning("Invalid JSON payload in queue: %s", exc)
        except redis.exceptions.RedisError as exc:
            logging.warning("Redis error while consuming queue: %s", exc)
            # Run cleanup attempt even if queue read fails intermittently.
            try:
                if int(time.time()) - last_cleanup_epoch >= EXPIRATION_CLEANUP_INTERVAL_SECONDS:
                    _cleanup_expired_secrets(client)
                    last_cleanup_epoch = int(time.time())
            except Exception:
                logging.exception("Unexpected error during cleanup fallback")
            time.sleep(2)
        except Exception as exc:
            logging.exception("Unexpected worker error: %s", exc)
            time.sleep(1)

    logging.info("Worker stopped.")
