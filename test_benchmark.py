import json
import re
from collections import Counter
from pathlib import Path

import pytest

from t2s.backends import OracleBackend
from t2s.benchmark_db import build_all, schema_of
from t2s.evaluate import custom_items, run, summarize
from t2s.prompts import build_user_message
from t2s.sql_utils import execute

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "benchmark" / "questions.jsonl"


@pytest.fixture(scope="module")
def dbs(tmp_path_factory):
    return build_all(tmp_path_factory.mktemp("dbs"))


@pytest.fixture(scope="module")
def questions():
    return [json.loads(line) for line in QUESTIONS.read_text(encoding="utf-8").splitlines()]


def test_questions_well_formed(questions):
    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids)) == 60
    assert Counter(q["db"] for q in questions) == {"shop": 20, "university": 20, "library": 20}
    for q in questions:
        assert q["difficulty"] in {"easy", "medium", "hard"}
        assert q["question_ru"].strip() and q["question_en"].strip()


def test_gold_queries_run_and_are_not_empty(dbs, questions):
    for q in questions:
        res = execute(dbs[q["db"]], q["sql"])
        assert res.ok, (q["id"], res.error)
        assert res.rows, f"{q['id']}: эталон вернул пустой результат"
        assert any(v is not None for row in res.rows for v in row), q["id"]


def test_quoted_values_match_gold_sql(questions):
    for q in questions:
        literals = set(re.findall(r"'([^']+)'", q["sql"])) - {"%Y"}
        for lang in ("ru", "en"):
            quoted = set(re.findall(r"(?<![A-Za-z])'([^']+)'", q[f"question_{lang}"]))
            assert quoted == {x for x in literals if x not in {"2025"}}, (q["id"], lang)


def test_databases_are_deterministic(tmp_path):
    a = build_all(tmp_path / "a")
    b = build_all(tmp_path / "b")
    for name in a:
        assert a[name].read_bytes() == b[name].read_bytes(), name


def test_schema_is_create_statements(dbs):
    schema = schema_of(dbs["shop"])
    assert schema.count("CREATE TABLE") == 4
    assert "order_items" in schema


def test_oracle_scores_100(tmp_path):
    items = custom_items(str(QUESTIONS), str(tmp_path / "dbs"), ["ru", "en"])
    backend = OracleBackend({build_user_message(i["schema"], i["question"]): i["gold"]
                             for i in items})
    summary = summarize(run(backend, items, batch_size=16, log_every=10_000))
    assert summary["custom"]["n"] == 120
    assert summary["custom"]["accuracy"] == 100.0
