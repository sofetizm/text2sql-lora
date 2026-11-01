import sqlite3

from t2s.sql_utils import (
    execute,
    extract_sql,
    has_order_by,
    is_read_only,
    normalize_sql,
    results_match,
)


def test_extract_from_code_fence_with_explanation():
    text = "Конечно! Вот запрос:\n```sql\nSELECT name\nFROM users;\n```\nОн выбирает имена."
    assert extract_sql(text) == "SELECT name FROM users"


def test_extract_plain_and_cut_at_semicolon():
    assert extract_sql("SELECT 1; SELECT 2;") == "SELECT 1"
    assert extract_sql("The answer is: select count(*) from t") == "select count(*) from t"


def test_extract_cte_and_empty():
    assert extract_sql("WITH x AS (SELECT 1) SELECT * FROM x").startswith("WITH x")
    assert extract_sql("") == ""
    assert extract_sql("не знаю") == "не знаю"  # пусть лучше упадёт на выполнении


def test_normalize_sql():
    a = 'SELECT  name FROM t WHERE city = "Kazan";'
    b = "select name from t where city='Kazan'"
    assert normalize_sql(a) == normalize_sql(b)


def test_read_only_guard():
    assert is_read_only("SELECT * FROM t")
    assert not is_read_only("DROP TABLE t")
    assert not is_read_only("SELECT 1; DELETE FROM t")
    assert execute(":memory:", "DROP TABLE t").error == "not a read-only query"


def test_results_match_rules():
    assert results_match([("a", 1)], [(1, "a")], ordered=False)          # порядок столбцов
    assert results_match([(3.333333,)], [(3.33,)], ordered=False)        # округление
    assert results_match([(10.0,)], [(10,)], ordered=False)              # 10.0 == 10
    assert results_match([(1,), (2,)], [(2,), (1,)], ordered=False)
    assert not results_match([(1,), (2,)], [(2,), (1,)], ordered=True)
    assert results_match([("x",)], [("x",), ("x",)], ordered=False)      # DISTINCT не штрафуем
    assert not results_match([(1,)], [(2,)], ordered=False)


def test_has_order_by():
    assert has_order_by("select a from t ORDER  BY a")
    assert not has_order_by("select border from t")


def test_execute_timeout(tmp_path):
    db = tmp_path / "t.sqlite"
    sqlite3.connect(db).close()
    infinite = "WITH RECURSIVE r(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM r) SELECT max(n) FROM r"
    res = execute(db, infinite, timeout_s=0.3)
    assert res.error == "timeout"


def test_execute_reports_schema_errors(tmp_path):
    db = tmp_path / "t.sqlite"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE t (a INTEGER)")
    conn.close()
    assert "no such column" in execute(db, "SELECT b FROM t").error
    assert execute(db, "SELECT a FROM t").rows == []
