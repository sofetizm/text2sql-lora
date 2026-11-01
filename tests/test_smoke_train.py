import json
import sys

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("peft")

from tiny_model import make_tiny_model

from t2s import train as train_mod
from t2s.backends import HFBackend
from t2s.prompts import build_messages

pytestmark = pytest.mark.slow


def test_label_masking(tmp_path):
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(make_tiny_model(tmp_path / "m"))
    ex = {"schema": "CREATE TABLE t (id INTEGER);", "question": "How many?",
          "sql": "SELECT COUNT(*) FROM t"}
    item = train_mod.tokenize_example(tok, ex, max_len=512)
    supervised = [t for t, lbl in zip(item["input_ids"], item["labels"], strict=True) if lbl != -100]
    text = tok.decode(supervised)
    assert "SELECT COUNT(*) FROM t" in text
    assert "CREATE TABLE" not in text
    assert train_mod.tokenize_example(tok, ex, max_len=10) is None


def test_train_and_generate(tmp_path, monkeypatch):
    model_dir = make_tiny_model(tmp_path / "model")
    rows = [{"schema": "CREATE TABLE t (id INTEGER, name TEXT);",
             "question": f"What is the name of item {i}?",
             "sql": f"SELECT name FROM t WHERE id = {i}"} for i in range(24)]
    for split in ("train", "val"):
        with open(tmp_path / f"{split}.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(f"""
model_name: {model_dir}
train_file: {tmp_path / 'train.jsonl'}
val_file: {tmp_path / 'val.jsonl'}
output_dir: {tmp_path / 'out'}
load_in_4bit: false
max_seq_length: 512
lora: {{r: 4, alpha: 8, dropout: 0.0, target_modules: [q_proj, v_proj]}}
training:
  max_steps: 4
  per_device_train_batch_size: 4
  learning_rate: 1.0e-3
  logging_steps: 1
  eval_steps: 2
  save_steps: 2
""")
    monkeypatch.setattr(sys, "argv", ["train", "--config", str(cfg)])
    train_mod.main()

    adapter = tmp_path / "out" / "adapter"
    assert (adapter / "adapter_config.json").exists()
    meta = json.loads((tmp_path / "out" / "train_meta.json").read_text())
    assert meta["trainable_params"] < meta["total_params"]

    backend = HFBackend(str(model_dir), adapter=str(adapter), max_new_tokens=8)
    gens = backend.generate([build_messages(r["schema"], r["question"]) for r in rows[:3]])
    assert len(gens) == 3 and all(g.output_tokens <= 8 for g in gens)
