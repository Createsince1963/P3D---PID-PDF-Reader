"""Named JSON profiles used for table and preview layouts.

The store deliberately receives its file path from the consuming application.
The GUI kit therefore never decides where a tool keeps its configuration.
Extracted from the AZ v0.62 preview-settings pattern.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ViewSettingsStore:
    """Persist named settings profiles grouped by a caller-defined key."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def _read(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (OSError, TypeError, ValueError):
            return {}

    @staticmethod
    def _entry(payload: dict[str, Any], key: str) -> dict[str, Any]:
        value = payload.get(key, {})
        if not isinstance(value, dict):
            return {"profiles": {}, "last_profile": "Default"}
        if isinstance(value.get("profiles"), dict):
            return value
        return {"profiles": {"Default": value} if value else {}, "last_profile": "Default"}

    def profiles(self, key: str) -> list[str]:
        return sorted(self._entry(self._read(), key)["profiles"], key=str.casefold)

    def last_profile(self, key: str) -> str:
        entry = self._entry(self._read(), key)
        last = str(entry.get("last_profile", "Default"))
        return last if last in entry["profiles"] else next(iter(self.profiles(key)), "Default")

    def load(self, key: str, profile: str | None = None) -> dict[str, Any]:
        entry = self._entry(self._read(), key)
        value = entry["profiles"].get(profile or self.last_profile(key), {})
        return value if isinstance(value, dict) else {}

    def save(self, key: str, profile: str, settings: dict[str, Any]) -> None:
        name = profile.strip()
        if not name:
            raise ValueError("A settings profile needs a name.")
        payload = self._read()
        entry = self._entry(payload, key)
        entry["profiles"][name] = settings
        entry["last_profile"] = name
        payload[key] = entry
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
