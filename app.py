"""Демо: вопрос на русском или английском → SQL → результат прямо из базы.

Локально:          MODEL=Qwen/Qwen2.5-1.5B-Instruct ADAPTER=outputs/.../adapter python app.py
Hugging Face Space: укажи MODEL и ADAPTER (id адаптера на Hub) в настройках Space.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import gradio as gr  # noqa: E402

from t2s.backends import HFBackend  # noqa: E402
from t2s.benchmark_db import build_all, schema_of  # noqa: E402
from t2s.prompts import build_messages  # noqa: E402
from t2s.sql_utils import execute, extract_sql  # noqa: E402

MODEL = os.environ.get("MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
ADAPTER = os.environ.get("ADAPTER") or None

DBS = build_all(Path(__file__).parent / "benchmark" / "dbs")
SCHEMAS = {name: schema_of(path) for name, path in DBS.items()}
backend = HFBackend(MODEL, ADAPTER, load_in_4bit=bool(os.environ.get("LOAD_IN_4BIT")))

EXAMPLES = [
    ["shop", "Какие 3 товара продаются лучше всего по количеству?"],
    ["shop", "Сколько клиентов в каждом городе?"],
    ["university", "Какой средний балл по курсу 'Databases'?"],
    ["library", "Which genre is borrowed most often?"],
]


def answer(db: str, question: str):
    gen = backend.generate([build_messages(SCHEMAS[db], question)])[0]
    sql = extract_sql(gen.text)
    res = execute(DBS[db], sql)
    if not res.ok:
        return sql, [[f"Ошибка: {res.error}"]], f"{gen.latency_s:.2f} с"
    return sql, [list(r) for r in res.rows[:50]] or [["(пусто)"]], f"{gen.latency_s:.2f} с"


with gr.Blocks(title="Text-to-SQL с LoRA") as demo:
    gr.Markdown(f"# Text-to-SQL\nМодель: `{MODEL}`" + (f" + адаптер `{ADAPTER}`" if ADAPTER else ""))
    with gr.Row():
        with gr.Column():
            db = gr.Dropdown(list(DBS), value="shop", label="База данных")
            schema = gr.Code(SCHEMAS["shop"], language="sql", label="Схема", interactive=False)
            question = gr.Textbox(label="Вопрос", lines=2)
            run = gr.Button("Сгенерировать SQL", variant="primary")
        with gr.Column():
            sql = gr.Code(language="sql", label="SQL от модели")
            table = gr.Dataframe(label="Результат", wrap=True)
            latency = gr.Textbox(label="Время генерации")
    db.change(lambda d: SCHEMAS[d], db, schema)
    run.click(answer, [db, question], [sql, table, latency])
    question.submit(answer, [db, question], [sql, table, latency])
    gr.Examples(EXAMPLES, [db, question])

if __name__ == "__main__":
    demo.launch()
