from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.main as worker_main


class FakeRedis:
    def __init__(self, members):
        self._members = members
        self.removed = []

    def zrangebyscore(self, key, min_score, max_score):
        del key, min_score, max_score
        return list(self._members)

    def zrem(self, key, member):
        self.removed.append((key, member))


def build_test_db_session_factory():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    worker_main.Base.metadata.create_all(bind=engine)
    return Session


def test_cleanup_expired_secrets_deletes_matching_row_and_zset_member(monkeypatch):
    testing_session_factory = build_test_db_session_factory()
    monkeypatch.setattr(worker_main, "SessionLocal", testing_session_factory)

    db = testing_session_factory()
    try:
        db.add(worker_main.Secret(id=1, owner="alice"))
        db.commit()
    finally:
        db.close()

    fake_redis = FakeRedis(["alice:1"])
    worker_main._cleanup_expired_secrets(fake_redis)

    db = testing_session_factory()
    try:
        secret = db.query(worker_main.Secret).filter_by(id=1, owner="alice").first()
        assert secret is None
    finally:
        db.close()

    assert (
        worker_main.EXPIRATION_ZSET_KEY,
        "alice:1",
    ) in fake_redis.removed


def test_cleanup_expired_secrets_removes_malformed_members(monkeypatch):
    testing_session_factory = build_test_db_session_factory()
    monkeypatch.setattr(worker_main, "SessionLocal", testing_session_factory)

    fake_redis = FakeRedis(["malformed-member"])
    worker_main._cleanup_expired_secrets(fake_redis)

    assert (
        worker_main.EXPIRATION_ZSET_KEY,
        "malformed-member",
    ) in fake_redis.removed
