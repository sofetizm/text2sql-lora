"""OpenAI-совместимый бэкенд на фейковом клиенте: без сети и ключей."""
import time
from types import SimpleNamespace

from t2s.backends import OpenAIBackend
from t2s.evaluate import run, summarize


class FakeCompletions:
    def __init__(self, fail_on=()):
        self.calls, self.fail_on = [], set(fail_on)

    def create(self, **kwargs):
        self.calls.append((time.monotonic(), kwargs))
        if len(self.calls) in self.fail_on:
            raise RuntimeError("rate limit")
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="```sql\nSELECT 1;\n```"))],
            usage=SimpleNamespace(prompt_tokens=1000, completion_tokens=100))


def _backend(**kw):
    completions = FakeCompletions(kw.pop("fail_on", ()))
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return OpenAIBackend("m", price_in=0.15, price_out=0.60, client=client, **kw), completions


def test_cost_and_reasoning_effort():
    backend, calls = _backend(reasoning_effort="low", max_tokens=2048)
    g = backend.generate([[{"role": "user", "content": "q"}]])[0]
    assert g.text.startswith("```sql")
    assert abs(g.cost_usd - (1000 * 0.15 + 100 * 0.60) / 1e6) < 1e-12
    kwargs = calls.calls[0][1]
    assert kwargs["reasoning_effort"] == "low" and kwargs["max_tokens"] == 2048


def test_rpm_spacing():
    backend, calls = _backend(rpm=600)  # 0.1 с между запросами
    backend.generate([[{"role": "user", "content": "q"}]] * 3)
    times = [t for t, _ in calls.calls]
    assert all(b - a >= 0.09 for a, b in zip(times, times[1:], strict=False))


def test_api_error_is_reported_not_crashing():
    backend, _ = _backend(fail_on={2})
    items = [{"id": f"h{i}", "suite": "heldout", "lang": "en", "question": "q",
              "schema": "CREATE TABLE t (a INT);", "gold": "SELECT 1"} for i in range(3)]
    records = run(backend, items, batch_size=1, log_every=100)
    assert [r.get("error_type") for r in records] == [None, "api_error", None]
    assert summarize(records)["heldout"]["accuracy"] == round(200 / 3, 1)
