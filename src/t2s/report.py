from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def _get(d: dict, *keys, default="—"):
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return default if d is None else d


def load_reports(results_dir: Path) -> list[dict]:
    reports = [json.loads(p.read_text(encoding="utf-8"))
               for p in sorted(results_dir.glob("*.json"))]
    return [r for r in reports if "summary" in r]


def markdown_table(reports: list[dict]) -> str:
    head = ("| Модель | Свой бенчмарк, RU | Свой бенчмарк, EN | Easy | Medium | Hard "
            "| Held-out EM | Held-out выполнимо | Задержка, с | Токенов/с | $ / 1000 запросов |")
    sep = "|" + "---|" * 11
    rows = [head, sep]
    for r in reports:
        s = r["summary"]
        rows.append("| " + " | ".join(str(x) for x in [
            f"**{r['name']}**",
            _get(s, "custom", "by_lang", "ru"), _get(s, "custom", "by_lang", "en"),
            _get(s, "custom", "by_difficulty", "easy"), _get(s, "custom", "by_difficulty", "medium"),
            _get(s, "custom", "by_difficulty", "hard"),
            _get(s, "heldout", "accuracy"), _get(s, "heldout", "executable"),
            _get(s, "speed", "latency_mean_s"), _get(s, "speed", "output_tokens_per_s"),
            _get(s, "cost", "per_1000_queries_usd"),
        ]) + " |")
    return "\n".join(rows)


def errors_table(reports: list[dict]) -> str:
    kinds = sorted({k for r in reports for k in _get(r["summary"], "custom", "errors", default={})})
    if not kinds:
        return ""
    names = {"schema_error": "несуществующие таблицы/столбцы", "syntax_error": "синтаксис",
             "wrong_result": "выполнился, но ответ неверный", "no_sql": "нет SQL в ответе",
             "timeout": "таймаут", "api_error": "ошибка API"}
    rows = ["| Модель | " + " | ".join(names.get(k, k) for k in kinds) + " |",
            "|---|" + "---|" * len(kinds)]
    for r in reports:
        errs = Counter(_get(r["summary"], "custom", "errors", default={}))
        rows.append(f"| **{r['name']}** | " + " | ".join(str(errs[k]) for k in kinds) + " |")
    return "\n".join(rows)


def plot(reports: list[dict], path: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    groups = ["ru", "en"]
    width = 0.8 / max(len(reports), 1)
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, r in enumerate(reports):
        vals = [_get(r["summary"], "custom", "by_lang", g, default=0) for g in groups]
        xs = [j + i * width for j in range(len(groups))]
        bars = ax.bar(xs, vals, width, label=r["name"])
        ax.bar_label(bars, fmt="%.0f", fontsize=8, padding=2)
    ax.set_xticks([j + width * (len(reports) - 1) / 2 for j in range(len(groups))])
    ax.set_xticklabels(["Вопросы на русском", "Вопросы на английском"])
    ax.set_ylabel("Execution accuracy, %")
    ax.set_ylim(0, 105)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    ax.set_title("Собственный бенчмарк: 60 вопросов × 3 базы")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results")
    args = parser.parse_args()
    results_dir = Path(args.results)
    reports = load_reports(results_dir)
    if not reports:
        raise SystemExit(f"в {results_dir} нет результатов — сначала запусти t2s.evaluate")

    parts = ["# Результаты", "", markdown_table(reports), ""]
    errs = errors_table(reports)
    if errs:
        parts += ["## Типы ошибок на своём бенчмарке", "", errs, ""]
    if plot(reports, results_dir / "accuracy.png"):
        parts += ["![accuracy](accuracy.png)", ""]
    (results_dir / "RESULTS.md").write_text("\n".join(parts), encoding="utf-8")
    print("\n".join(parts))


if __name__ == "__main__":
    main()
