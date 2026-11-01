from __future__ import annotations

import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

_FENCE_RE = re.compile(r"```(?:sql|sqlite)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
_START_RE = re.compile(r"\b(SELECT|WITH)\b", re.IGNORECASE)
_FORBIDDEN_RE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|PRAGMA|VACUUM)\b",
    re.IGNORECASE,
)


def extract_sql(text: str) -> str:
    if not text:
        return ""
    fence = _FENCE_RE.search(text)
    if fence:
        text = fence.group(1)
    start = _START_RE.search(text)
    if start:
        text = text[start.start():]
    text = text.split(";")[0]
    return " ".join(text.split()).strip()


def normalize_sql(sql: str) -> str:
    sql = sql.strip().rstrip(";").replace('"', "'")
    sql = re.sub(r"\s*([(),=<>])\s*", r"\1", sql)
    return " ".join(sql.lower().split())


def is_read_only(sql: str) -> bool:
    return bool(_START_RE.match(sql.strip())) and not _FORBIDDEN_RE.search(sql)


@dataclass
class ExecResult:
    rows: list[tuple] | None
    error: str | None
    seconds: float

    @property
    def ok(self) -> bool:
        return self.error is None


def execute(db: str | Path | sqlite3.Connection, sql: str, timeout_s: float = 5.0,
            max_rows: int = 10_000) -> ExecResult:
    if not is_read_only(sql):
        return ExecResult(None, "not a read-only query", 0.0)

    own_conn = not isinstance(db, sqlite3.Connection)
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True) if own_conn else db
    deadline = time.monotonic() + timeout_s
    conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 10_000)
    started = time.monotonic()
    try:
        rows = conn.execute(sql).fetchmany(max_rows)
        return ExecResult(rows, None, time.monotonic() - started)
    except sqlite3.OperationalError as e:
        msg = "timeout" if "interrupted" in str(e) else f"{type(e).__name__}: {e}"
        return ExecResult(None, msg, time.monotonic() - started)
    except sqlite3.Error as e:
        return ExecResult(None, f"{type(e).__name__}: {e}", time.monotonic() - started)
    finally:
        conn.set_progress_handler(None, 0)
        if own_conn:
            conn.close()


def _norm_value(v):
    if isinstance(v, float):
        v = round(v, 2)
        return int(v) if v.is_integer() else v
    return v


def _norm_row(row: tuple) -> tuple:
    return tuple(sorted((_norm_value(v) for v in row), key=lambda x: (str(type(x)), str(x))))


def has_order_by(sql: str) -> bool:
    return re.search(r"\border\s+by\b", sql, re.IGNORECASE) is not None


def results_match(gold: list[tuple], pred: list[tuple], ordered: bool) -> bool:

    g = [_norm_row(r) for r in gold]
    p = [_norm_row(r) for r in pred]
    if ordered:
        return g == p
    return set(g) == set(p)


def schema_from_create_statements(context: str) -> sqlite3.Connection:

    conn = sqlite3.connect(":memory:")
    conn.executescript(context)
    return conn
