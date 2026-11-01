from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path

from .sql_utils import execute, schema_from_create_statements

_DQ_LITERAL = re.compile(r'"([^"]*)"')


def clean_context(context: str) -> str:
    tables = re.split(r",\s*(?=CREATE TABLE)", context.strip())
    return "\n".join(t.strip().rstrip(";") + ";" for t in tables)


def clean_answer(sql: str) -> str:
    """Строковые литералы в "двойных" кавычках → в 'одинарные' (стандарт SQL)."""
    def repl(m: re.Match) -> str:
        return "'" + m.group(1).replace("'", "''") + "'"
    return " ".join(_DQ_LITERAL.sub(repl, sql).split()).rstrip(";")


def is_valid(context: str, sql: str) -> bool:
    try:
        conn = schema_from_create_statements(context)
    except Exception:
        return False
    try:
        return execute(conn, sql, timeout_s=1.0).ok
    finally:
        conn.close()


def load_records(dataset: str) -> list[dict]:
    from datasets import load_dataset

    ds = load_dataset(dataset, split="train")
    return [{"schema": r["context"], "question": r["question"], "sql": r["answer"]} for r in ds]


def prepare(records: list[dict], n_train: int, n_val: int, n_test: int,
            seed: int = 13, max_chars: int = 2500) -> tuple[dict[str, list[dict]], dict]:
    stats = {"raw": len(records), "dropped_duplicates": 0, "dropped_too_long": 0,
             "dropped_invalid_sql": 0}
    seen, clean = set(), []
    for r in records:
        schema, sql = clean_context(r["schema"]), clean_answer(r["sql"])
        question = " ".join(r["question"].split())
        key = (question.lower(), schema)
        if key in seen:
            stats["dropped_duplicates"] += 1
            continue
        seen.add(key)
        if len(schema) + len(question) + len(sql) > max_chars:
            stats["dropped_too_long"] += 1
            continue
        if not is_valid(schema, sql):
            stats["dropped_invalid_sql"] += 1
            continue
        clean.append({"schema": schema, "question": question, "sql": sql})

    random.Random(seed).shuffle(clean)
    need = n_train + n_val + n_test
    if len(clean) < need:
        raise ValueError(f"после очистки осталось {len(clean)} примеров, нужно {need}")
    splits = {
        "test": clean[:n_test],
        "val": clean[n_test:n_test + n_val],
        "train": clean[n_test + n_val:need],
    }
    stats.update({"clean": len(clean), **{f"n_{k}": len(v) for k, v in splits.items()}})
    return splits, stats


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="b-mc2/sql-create-context")
    parser.add_argument("--out", default="data")
    parser.add_argument("--n-train", type=int, default=15000)
    parser.add_argument("--n-val", type=int, default=500)
    parser.add_argument("--n-test", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    splits, stats = prepare(load_records(args.dataset), args.n_train, args.n_val,
                            args.n_test, args.seed)
    for name, rows in splits.items():
        write_jsonl(out / f"{name}.jsonl", rows)
    (out / "stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
