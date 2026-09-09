"""Ephemeral Session Storage Manager (DPDP Act 2023 Compliant).

Handles temporary patient data storage at the MediKiosk terminal.
Features:
- Primary storage via Redis with strict 15-minute TTL auto-expiration.
- Transparent fallback to an in-memory TTL dictionary when Redis is unavailable.
- Immediate zero-knowledge purging post-consultation to guarantee patient privacy.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("medikiosk.session")

DEFAULT_TTL_SECONDS = 900  # 15 minutes per DPDP Act kiosk guidelines


class SessionManager:
    """Manages ephemeral kiosk patient sessions with Redis or in-memory TTL fallback."""

    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = DEFAULT_TTL_SECONDS) -> None:
        self.default_ttl = default_ttl
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis_client = None
        self._redis_connected = False

        # In-memory thread-safe fallback store
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        # Attempt Redis connection
        self._init_redis()

    def _init_redis(self) -> None:
        """Attempt to connect to Redis; gracefully fallback on failure."""
        try:
            import redis  # type: ignore

            client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=1.0,
                socket_connect_timeout=1.0,
            )
            client.ping()
            self._redis_client = client
            self._redis_connected = True
            logger.info("Connected to Redis at %s for ephemeral session storage.", self.redis_url)
        except Exception as exc:
            self._redis_client = None
            self._redis_connected = False
            logger.info(
                "Redis unavailable (%s). Operating in-memory with strict TTL auto-purging.",
                type(exc).__name__,
            )

    @property
    def is_using_redis(self) -> bool:
        """Check if Redis backend is active."""
        if not self._redis_connected or self._redis_client is None:
            return False
        try:
            self._redis_client.ping()
            return True
        except Exception:
            self._redis_connected = False
            return False

    def create_session(
        self,
        patient_id: str,
        data: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Store an ephemeral session with 15-minute auto-expiry (TTL).

        Parameters
        ----------
        patient_id : str
            Patient ABHA identifier or kiosk registration token.
        data : Optional[Dict[str, Any]]
            Initial session payload (voice transcript, OCR data, vitals, etc.).
        ttl_seconds : Optional[int]
            TTL window in seconds. Defaults to 900s (15 minutes).

        Returns
        -------
        Dict[str, Any]
            Session metadata dictionary containing session_id and expiry.
        """
        ttl = ttl_seconds or self.default_ttl
        session_id = f"kiosk_sess_{uuid.uuid4().hex[:16]}"
        now = time.time()
        created_at_iso = datetime.now(timezone.utc).isoformat()
        expires_at_iso = datetime.fromtimestamp(now + ttl, tz=timezone.utc).isoformat()

        session_record = {
            "session_id": session_id,
            "patient_id": patient_id,
            "created_at": created_at_iso,
            "expires_at": expires_at_iso,
            "ttl_seconds": ttl,
            "data": data or {},
        }

        # Try Redis first
        if self.is_using_redis:
            try:
                key = f"medikiosk:session:{session_id}"
                self._redis_client.setex(key, ttl, json.dumps(session_record))
                logger.info("Created Redis ephemeral session %s (TTL: %ds)", session_id, ttl)
                return {
                    **session_record,
                    "storage_backend": "redis",
                    "ttl_remaining_seconds": ttl,
                }
            except Exception as exc:
                logger.warning("Redis write failed (%s); falling back to in-memory store.", exc)
                self._redis_connected = False

        # Fallback to in-memory TTL dictionary
        with self._lock:
            self._purge_expired_memory_locked()
            self._memory_store[session_id] = {
                "record": session_record,
                "expiry_timestamp": now + ttl,
            }

        logger.info("Created In-Memory ephemeral session %s (TTL: %ds)", session_id, ttl)
        return {
            **session_record,
            "storage_backend": "in_memory",
            "ttl_remaining_seconds": ttl,
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve current kiosk state from Redis or in-memory store.

        Parameters
        ----------
        session_id : str
            Unique session identifier.

        Returns
        -------
        Optional[Dict[str, Any]]
            Session dictionary if active and unexpired; None otherwise.
        """
        clean_id = session_id.strip()

        # Try Redis
        if self.is_using_redis:
            try:
                key = f"medikiosk:session:{clean_id}"
                raw = self._redis_client.get(key)
                if raw:
                    remaining_ttl = self._redis_client.ttl(key)
                    record = json.loads(raw)
                    return {
                        **record,
                        "storage_backend": "redis",
                        "ttl_remaining_seconds": max(0, remaining_ttl),
                    }
                return None
            except Exception as exc:
                logger.warning("Redis read failed (%s); checking in-memory store.", exc)
                self._redis_connected = False

        # Check in-memory store
        with self._lock:
            if clean_id not in self._memory_store:
                return None

            entry = self._memory_store[clean_id]
            now = time.time()
            remaining = int(entry["expiry_timestamp"] - now)

            # Enforce strict TTL expiration
            if remaining <= 0:
                del self._memory_store[clean_id]
                logger.info("Session %s has expired and was auto-purged.", clean_id)
                return None

            record = entry["record"]
            return {
                **record,
                "storage_backend": "in_memory",
                "ttl_remaining_seconds": remaining,
            }

    def update_session(self, session_id: str, new_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Merge additional clinical/kiosk data into an active session without resetting expiry.

        Parameters
        ----------
        session_id : str
            Active session identifier.
        new_data : Dict[str, Any]
            Key-values to update in the session's data dictionary.

        Returns
        -------
        Optional[Dict[str, Any]]
            Updated session record, or None if expired/not found.
        """
        existing = self.get_session(session_id)
        if not existing:
            return None

        # Merge data
        existing["data"].update(new_data)
        remaining_ttl = existing.get("ttl_remaining_seconds", self.default_ttl)

        # Write back
        if self.is_using_redis:
            try:
                key = f"medikiosk:session:{session_id}"
                self._redis_client.setex(key, max(1, remaining_ttl), json.dumps(existing))
                return existing
            except Exception:
                self._redis_connected = False

        with self._lock:
            if session_id in self._memory_store:
                self._memory_store[session_id]["record"] = existing
                return existing

        return None

    def purge_session(self, session_id: str) -> bool:
        """Immediately wipe all patient data upon successful handover to HIS/Doctor screen.

        Ensures full compliance with India's DPDP Act 2023 zero-retention mandate.

        Parameters
        ----------
        session_id : str
            Session identifier to erase immediately.

        Returns
        -------
        bool
            True if session was found and wiped; False if not found.
        """
        clean_id = session_id.strip()
        purged = False

        # Erase from Redis
        if self.is_using_redis:
            try:
                key = f"medikiosk:session:{clean_id}"
                count = self._redis_client.delete(key)
                if count > 0:
                    purged = True
            except Exception as exc:
                logger.warning("Redis delete failed (%s); checking in-memory store.", exc)
                self._redis_connected = False

        # Erase from in-memory store
        with self._lock:
            if clean_id in self._memory_store:
                del self._memory_store[clean_id]
                purged = True

        logger.info(
            "DPDP Act 2023 Compliance: Session %s purged from storage (result: %s).",
            clean_id,
            purged,
        )
        return purged

    def _purge_expired_memory_locked(self) -> None:
        """Housekeeping: evict stale sessions from in-memory dictionary."""
        now = time.time()
        expired_keys = [
            k for k, v in self._memory_store.items() if v["expiry_timestamp"] <= now
        ]
        for k in expired_keys:
            del self._memory_store[k]


# Singleton session manager
session_manager = SessionManager()


# Convenience functional interface
def create_session(
    patient_id: str,
    data: Optional[Dict[str, Any]] = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> Dict[str, Any]:
    """Store an ephemeral patient session."""
    return session_manager.create_session(patient_id, data, ttl_seconds)


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve current kiosk session."""
    return session_manager.get_session(session_id)


def update_session(session_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update active kiosk session with new clinical attributes."""
    return session_manager.update_session(session_id, data)


def purge_session(session_id: str) -> bool:
    """Immediately wipe patient data post-consultation."""
    return session_manager.purge_session(session_id)

