"""Оценка моделей на двух наборах.

* custom  — собственный бенчмарк: 60 вопросов к трём базам с данными, на русском и
            английском. Метрика — execution accuracy: запрос модели выполняется,
            и его результат сравнивается с результатом эталона.
* heldout — отложенная часть sql-create-context (те же «домен» и стиль, что в обучении).
            Метрики — exact match после нормализации и доля выполнимых запросов.

Примеры:
  python -m t2s.evaluate --name base --backend hf --model Qwen/Qwen2.5-1.5B-Instruct
  python -m t2s.evaluate --name lora --backend hf --model Qwen/Qwen2.5-1.5B-Instruct \\
      --adapter outputs/qwen1.5b-sql-lora/adapter
  python -m t2s.evaluate --name api --backend openai --model MODEL_NAME \\
      --price-in 0.15 --price-out 0.60
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import defaultdict
from pathlib import Path

from .backends import Backend, HFBackend, OpenAIBackend, OracleBackend
from .benchmark_db import build_all, schema_of
from .data import read_jsonl
from .prompts import build_messages
from .sql_utils import (
    ExecResult,
    execute,
    extract_sql,
    has_order_by,
    normalize_sql,
    results_match,
    schema_from_create_statements,
)


# ------------------------------------------------------------------ сбор заданий
def custom_items(questions_path: str, db_dir: str, langs: list[str]) -> list[dict]:
    dbs = build_all(db_dir)
    schemas = {name: schema_of(path) for name, path in dbs.items()}
    items = []
    for q in read_jsonl(questions_path):
        for lang in langs:
            items.append({
                "id": f"{q['id']}:{lang}", "suite": "custom", "lang": lang, "db": q["db"],
                "db_path": str(dbs[q["db"]]), "difficulty": q["difficulty"],
                "question": q[f"question_{lang}"], "schema": schemas[q["db"]], "gold": q["sql"],
            })
    return items


def heldout_items(test_path: str, limit: int | None) -> list[dict]:
    rows = read_jsonl(test_path)[:limit] if limit else read_jsonl(test_path)
    return [{"id": f"heldout-{i}", "suite": "heldout", "lang": "en", "question": r["question"],
             "schema": r["schema"], "gold": r["sql"]} for i, r in enumerate(rows)]


# ----------------------------------------------------------------------- оценка
def classify_error(pred_sql: str, pred_exec: ExecResult) -> str:
    if not pred_sql:
        return "no_sql"
    if pred_exec.error == "timeout":
        return "timeout"
    if pred_exec.error:
        msg = pred_exec.error.lower()
        if "no such column" in msg or "no such table" in msg:
            return "schema_error"  # выдуманные таблицы/столбцы — главная болезнь базовых моделей
        return "syntax_error"
    return "wrong_result"


def score_item(item: dict, raw_output: str) -> dict:
    pred_sql = extract_sql(raw_output)
    rec = {"pred_sql": pred_sql, "raw_output": raw_output}
    if item["suite"] == "custom":
        gold = execute(item["db_path"], item["gold"])
        pred = execute(item["db_path"], pred_sql) if pred_sql else ExecResult(None, "empty", 0.0)
        ok = pred.ok and results_match(gold.rows, pred.rows, has_order_by(item["gold"]))
        rec.update({"executable": pred.ok, "correct": ok,
                    "error_type": None if ok else classify_error(pred_sql, pred),
                    "exec_error": pred.error})
    else:
        conn = schema_from_create_statements(item["schema"])
        try:
            pred = execute(conn, pred_sql, timeout_s=1.0) if pred_sql else None
        finally:
            conn.close()
        rec.update({"executable": bool(pred and pred.ok),
                    "correct": normalize_sql(pred_sql) == normalize_sql(item["gold"])})
    return rec


def _pct(xs: list[bool]) -> float:
    return round(100 * sum(xs) / len(xs), 1) if xs else 0.0


def summarize(records: list[dict]) -> dict:
    summary: dict = {}
    for suite in sorted({r["suite"] for r in records}):
        rs = [r for r in records if r["suite"] == suite]
        s = {"n": len(rs), "accuracy": _pct([r["correct"] for r in rs]),
             "executable": _pct([r["executable"] for r in rs])}
        for key in ("lang", "difficulty", "db"):
            groups = defaultdict(list)
            for r in rs:
                if key in r:
                    groups[r[key]].append(r["correct"])
            if len(groups) > 1 or key == "lang":
                s[f"by_{key}"] = {k: _pct(v) for k, v in sorted(groups.items())}
        errors = defaultdict(int)
        for r in rs:
            if r.get("error_type"):
                errors[r["error_type"]] += 1
        if errors:
            s["errors"] = dict(sorted(errors.items(), key=lambda kv: -kv[1]))
        summary[suite] = s

    lat = [r["latency_s"] for r in records if r["latency_s"] > 0]
    out_tok = sum(r["output_tokens"] for r in records)
    gen_time = sum(lat)
    summary["speed"] = {
        "latency_mean_s": round(statistics.mean(lat), 3) if lat else None,
        "latency_p95_s": round(sorted(lat)[int(0.95 * (len(lat) - 1))], 3) if lat else None,
        "output_tokens_per_s": round(out_tok / gen_time, 1) if gen_time else None,
    }
    cost = sum(r["cost_usd"] for r in records)
    summary["cost"] = {"total_usd": round(cost, 4),
                       "per_1000_queries_usd": round(1000 * cost / len(records), 4)}
    return summary


def run(backend: Backend, items: list[dict], batch_size: int = 8, log_every: int = 20) -> list[dict]:
    records = []
    for start in range(0, len(items), batch_size):
        chunk = items[start:start + batch_size]
        gens = backend.generate([build_messages(it["schema"], it["question"]) for it in chunk])
        for it, g in zip(chunk, gens, strict=True):
            rec = {k: v for k, v in it.items() if k not in ("schema", "db_path")}
            rec.update(score_item(it, g.text))
            rec.update({"latency_s": g.latency_s, "input_tokens": g.input_tokens,
                        "output_tokens": g.output_tokens, "cost_usd": g.cost_usd})
            records.append(rec)
        done = len(records)
        if done % log_every < batch_size or done == len(items):
            acc = _pct([r["correct"] for r in records])
            print(f"  {done}/{len(items)}  accuracy so far: {acc}%", flush=True)
    return records


def make_backend(args, items: list[dict]) -> Backend:
    if args.backend == "hf":
        return HFBackend(args.model, args.adapter, args.load_in_4bit, args.max_new_tokens)
    if args.backend == "openai":
        return OpenAIBackend(args.model, args.price_in, args.price_out, args.max_new_tokens)
    if args.backend == "oracle":
        from .prompts import build_user_message
        return OracleBackend({build_user_message(i["schema"], i["question"]): i["gold"]
                              for i in items})
    raise ValueError(args.backend)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", required=True, help="подпись модели в отчёте, например base / lora")
    p.add_argument("--backend", choices=["hf", "openai", "oracle"], required=True)
    p.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    p.add_argument("--adapter", default=None, help="путь или id адаптера LoRA на HF Hub")
    p.add_argument("--load-in-4bit", action="store_true")
    p.add_argument("--suites", default="custom,heldout")
    p.add_argument("--langs", default="ru,en")
    p.add_argument("--questions", default="benchmark/questions.jsonl")
    p.add_argument("--db-dir", default="benchmark/dbs")
    p.add_argument("--heldout", default="data/test.jsonl")
    p.add_argument("--heldout-limit", type=int, default=300)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--max-new-tokens", type=int, default=256)
    p.add_argument("--price-in", type=float, default=0.0, help="USD за 1 млн входных токенов")
    p.add_argument("--price-out", type=float, default=0.0, help="USD за 1 млн выходных токенов")
    p.add_argument("--out", default="results")
    args = p.parse_args()

    suites = args.suites.split(",")
    items = []
    if "custom" in suites:
        items += custom_items(args.questions, args.db_dir, args.langs.split(","))
    if "heldout" in suites:
        if Path(args.heldout).exists():
            items += heldout_items(args.heldout, args.heldout_limit)
        else:
            print(f"[!] {args.heldout} не найден — пропускаю heldout (запусти python -m t2s.data)")

    backend = make_backend(args, items)
    batch = 1 if args.backend == "openai" else args.batch_size
    print(f"Оцениваю '{args.name}' на {len(items)} заданиях…")
    started = time.time()
    records = run(backend, items, batch)

    summary = summarize(records)
    report = {"name": args.name, **backend.describe(), "summary": summary,
              "wall_time_min": round((time.time() - started) / 60, 2)}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{args.name}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    with (out / f"{args.name}_predictions.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Результаты: {out / (args.name + '.json')}")


if __name__ == "__main__":
    main()
