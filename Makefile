MODEL   ?= Qwen/Qwen2.5-1.5B-Instruct
ADAPTER ?= outputs/qwen1.5b-sql-lora/adapter
CONFIG  ?= configs/qlora_qwen1.5b.yaml

.PHONY: install dbs data train eval-base eval-lora eval-api report compare test test-slow lint

install:
	pip install -r requirements.txt && pip install -e ".[dev]"

dbs:
	python -m t2s.benchmark_db --out benchmark/dbs

data:
	python -m t2s.data --out data

train:
	python -m t2s.train --config $(CONFIG)

eval-base:
	python -m t2s.evaluate --name base --backend hf --model $(MODEL) --load-in-4bit

eval-lora:
	python -m t2s.evaluate --name lora --backend hf --model $(MODEL) --adapter $(ADAPTER) --load-in-4bit

eval-api:
	python -m t2s.evaluate --name api --backend openai --model $(API_MODEL) \
		--price-in $(PRICE_IN) --price-out $(PRICE_OUT)

report:
	python -m t2s.report --results results

compare:
	python -m t2s.compare results/base_predictions.jsonl results/lora_predictions.jsonl

test:
	pytest

test-slow:
	pytest -m slow

lint:
	ruff check src tests app.py
