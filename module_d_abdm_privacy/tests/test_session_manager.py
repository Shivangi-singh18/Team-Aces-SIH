"""Unit tests for Ephemeral Session Manager & DPDP Compliance."""

import time
from module_d_abdm_privacy.session_manager import (
    SessionManager,
    create_session,
    get_session,
    purge_session,
    update_session,
)


def test_session_lifecycle():
    patient_id = "14-8921-3456-7890"
    init_data = {"token_number": 42, "language": "hi"}

    # 1. Create Session
    session = create_session(patient_id=patient_id, data=init_data, ttl_seconds=900)
    assert "session_id" in session
    session_id = session["session_id"]
    assert session["patient_id"] == patient_id
    assert session["ttl_remaining_seconds"] > 890

    # 2. Retrieve Session
    retrieved = get_session(session_id)
    assert retrieved is not None
    assert retrieved["data"]["token_number"] == 42

    # 3. Update Session
    updated = update_session(session_id, {"symptoms": ["chest_pain"]})
    assert updated is not None
    assert updated["data"]["token_number"] == 42
    assert updated["data"]["symptoms"] == ["chest_pain"]

    # 4. DPDP Act Zero-Knowledge Immediate Purge
    purged = purge_session(session_id)
    assert purged is True

    # 5. Verify Session Is Completely Erased
    after_purge = get_session(session_id)
    assert after_purge is None


def test_session_ttl_expiration():
    manager = SessionManager(default_ttl=1)  # 1 second TTL
    sess = manager.create_session("test-patient", {"key": "val"}, ttl_seconds=1)
    sid = sess["session_id"]

    # Immediate query succeeds
    assert manager.get_session(sid) is not None

    # Wait for TTL expiry
    time.sleep(1.2)

    # Subsequent query returns None due to auto-eviction
    assert manager.get_session(sid) is None

