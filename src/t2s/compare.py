"""Разбор ошибок: какие задания дообучение исправило, а какие сломало.

Запуск:  python -m t2s.compare results/base_predictions.jsonl results/lora_predictions.jsonl
Пишет results/compare_<a>_vs_<b>.md — полезно для раздела «Анализ ошибок» в README.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .data import read_jsonl


def compare(a_path: str, b_path: str, suite: str = "custom") -> tuple[str, dict]:
    a = {r["id"]: r for r in read_jsonl(a_path) if r["suite"] == suite}
    b = {r["id"]: r for r in read_jsonl(b_path) if r["suite"] == suite}
    common = sorted(a.keys() & b.keys())
    fixed = [i for i in common if not a[i]["correct"] and b[i]["correct"]]
    broken = [i for i in common if a[i]["correct"] and not b[i]["correct"]]
    both_wrong = [i for i in common if not a[i]["correct"] and not b[i]["correct"]]
    stats = {"total": len(common), "fixed": len(fixed), "broken": len(broken),
             "both_wrong": len(both_wrong)}

    name_a, name_b = Path(a_path).stem.replace("_predictions", ""), \
        Path(b_path).stem.replace("_predictions", "")
    lines = [f"# {name_a} → {name_b}", "",
             f"Заданий: {stats['total']}. Исправлено: **{stats['fixed']}**, "
             f"сломано: **{stats['broken']}**, ошибаются обе: {stats['both_wrong']}.", ""]
    for title, ids in [("Исправлено", fixed), ("Сломано", broken), ("Ошибаются обе", both_wrong)]:
        if not ids:
            continue
        lines += [f"## {title}", ""]
        for i in ids:
            lines += [
                f"### {i} ({a[i].get('difficulty', '')})", "", f"> {a[i]['question']}", "",
                f"- эталон: `{a[i]['gold']}`",
                f"- {name_a}: `{a[i]['pred_sql'] or '—'}` "
                f"({'верно' if a[i]['correct'] else a[i].get('error_type')})",
                f"- {name_b}: `{b[i]['pred_sql'] or '—'}` "
                f"({'верно' if b[i]['correct'] else b[i].get('error_type')})", ""]
    return "\n".join(lines), stats


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("before")
    p.add_argument("after")
    p.add_argument("--suite", default="custom")
    args = p.parse_args()
    text, stats = compare(args.before, args.after, args.suite)
    out = Path(args.after).parent / (
        f"compare_{Path(args.before).stem.replace('_predictions', '')}"
        f"_vs_{Path(args.after).stem.replace('_predictions', '')}.md")
    out.write_text(text, encoding="utf-8")
    print(stats)
    print(f"Отчёт: {out}")


if __name__ == "__main__":
    main()
