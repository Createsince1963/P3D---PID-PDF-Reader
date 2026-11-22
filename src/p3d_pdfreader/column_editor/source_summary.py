"""Short facts about the source of a table for the collapsed source bar (pure Python, no Qt)."""
from __future__ import annotations

from dataclasses import dataclass

SOURCE_TYPE_NAMES = {"dcf": "DCF Result", "xlsx": "External Excel", "plan": "App Table", "app": "App Table"}


@dataclass(frozen=True, slots=True)
class SourceSummary:
    name: str = ""
    source_type: str = ""
    area: str = ""
    rows: int | None = None
    columns: int | None = None
    fingerprint: str = ""        # "SHA-256 3fa9c2d41b7e, unchanged by reading"
    fingerprint_ok: bool = True
    lock: str = ""               # only for Excel sources: "no lock file" / "locked: ~$name.xlsx"

    def parts(self) -> list[str]:
        """The collapsed header, in the order of the specification."""
        out = [self.name or "(no source)", self.source_type, self.area]
        if self.rows is not None:
            out.append(f"{self.rows:,} rows")
        if self.columns is not None:
            out.append(f"{self.columns:,} columns")
        out.append(self.fingerprint or "no fingerprint")
        if self.lock:
            out.append(self.lock)
        return [p for p in out if p]


def summarize(table, area: str, lock: str = "") -> SourceSummary:
    """`table` is a SourceTable (or None). `lock` is the lock-file text of an Excel source ('' = not applicable)."""
    if table is None:
        return SourceSummary(area=area)
    meta = getattr(table, "meta", {}) or {}
    before = str(meta.get("sha256_before") or "")
    ok = str(meta.get("unchanged") or "") == "YES"
    if before:
        fp = f"SHA-256 {before[:12]}…, " + ("unchanged by reading" if ok else "CHANGED during reading")
    else:
        fp = ""
    kind = SOURCE_TYPE_NAMES.get(str(getattr(table, "source_type", "")), "App Table")
    return SourceSummary(name=str(getattr(table, "source_name", "")), source_type=kind, area=area,
                         rows=len(table.rows), columns=len(table.columns), fingerprint=fp,
                         fingerprint_ok=ok or not before, lock=lock if kind == "External Excel" else "")
