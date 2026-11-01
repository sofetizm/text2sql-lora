import json

from t2s.compare import compare
from t2s.data import clean_answer, clean_context, is_valid, prepare
from t2s.prompts import SYSTEM_PROMPT, build_messages
from t2s.report import errors_table, markdown_table


def test_clean_context_splits_tables():
    ctx = "CREATE TABLE a (x INTEGER), CREATE TABLE b (y VARCHAR)"
    assert clean_context(ctx) == "CREATE TABLE a (x INTEGER);\nCREATE TABLE b (y VARCHAR);"


def test_clean_answer_quotes():
    assert clean_answer('SELECT x FROM a WHERE name = "O\'Neil";') == \
        "SELECT x FROM a WHERE name = 'O''Neil'"


def test_is_valid():
    assert is_valid("CREATE TABLE a (x INTEGER);", "SELECT x FROM a")
    assert not is_valid("CREATE TABLE a (x INTEGER);", "SELECT y FROM a")


def _records(n):
    return [{"schema": "CREATE TABLE t (id INTEGER, name VARCHAR)",
             "question": f"What is the name of item {i}?",
             "sql": f'SELECT name FROM t WHERE id = {i}'} for i in range(n)]


def test_prepare_splits_dedupes_and_filters():
    recs = _records(50) + _records(5)  # 5 дублей
    recs.append({"schema": "CREATE TABLE t (id INTEGER)", "question": "broken",
                 "sql": "SELECT nope FROM t"})
    splits, stats = prepare(recs, n_train=30, n_val=5, n_test=10)
    assert stats["dropped_duplicates"] == 5
    assert stats["dropped_invalid_sql"] == 1
    assert [len(splits[k]) for k in ("train", "val", "test")] == [30, 5, 10]
    test_q = {r["question"] for r in splits["test"]}
    assert not test_q & {r["question"] for r in splits["train"]}  # нет утечки


def test_messages_format():
    msgs = build_messages("CREATE TABLE t (a INT);", "q?", "SELECT a FROM t")
    assert msgs[0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert "### Schema" in msgs[1]["content"] and "### Question" in msgs[1]["content"]
    assert msgs[2]["role"] == "assistant"


def _report(name, ru, errors):
    return {"name": name, "summary": {
        "custom": {"by_lang": {"ru": ru, "en": ru + 5},
                   "by_difficulty": {"easy": 90, "medium": 70, "hard": 40}, "errors": errors},
        "heldout": {"accuracy": 60, "executable": 95},
        "speed": {"latency_mean_s": 0.3, "output_tokens_per_s": 40},
        "cost": {"per_1000_queries_usd": 0}}}


def test_report_tables():
    reports = [_report("base", 30, {"schema_error": 20}), _report("lora", 70, {"wrong_result": 5})]
    table = markdown_table(reports)
    assert "**base**" in table and "| 70 | 75 |" in table
    errs = errors_table(reports)
    assert "несуществующие таблицы/столбцы" in errs and "| **lora** | 0 | 5 |" in errs


def test_compare(tmp_path):
    def write(path, flags):
        with open(path, "w", encoding="utf-8") as f:
            for i, ok in enumerate(flags):
                f.write(json.dumps({"id": f"q{i}", "suite": "custom", "question": "?",
                                    "gold": "SELECT 1", "pred_sql": "SELECT 1", "correct": ok,
                                    "error_type": None if ok else "wrong_result"}) + "\n")
    write(tmp_path / "base_predictions.jsonl", [False, True, False])
    write(tmp_path / "lora_predictions.jsonl", [True, False, False])
    text, stats = compare(str(tmp_path / "base_predictions.jsonl"),
                          str(tmp_path / "lora_predictions.jsonl"))
    assert stats == {"total": 3, "fixed": 1, "broken": 1, "both_wrong": 1}
    assert "## Исправлено" in text
