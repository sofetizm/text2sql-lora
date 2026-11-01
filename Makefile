MODEL   ?= Qwen/Qwen2.5-1.5B-Instruct
ADAPTER ?= outputs/qwen1.5b-sql-lora/adapter
CONFIG  ?= configs/qlora_qwen1.5b.yaml

.PHONY: install dbs data train eval-base eval-lora eval-api report compare test test-slow lint

install:          ## зависимости для обучения + сам пакет
	pip install -r requirements.txt && pip install -e ".[dev]"

dbs:              ## базы SQLite для своего бенчмарка
	python -m t2s.benchmark_db --out benchmark/dbs

data:             ## скачать и подготовить sql-create-context
	python -m t2s.data --out data

train:            ## QLoRA-обучение
	python -m t2s.train --config $(CONFIG)

eval-base:        ## базовая модель без дообучения
	python -m t2s.evaluate --name base --backend hf --model $(MODEL) --load-in-4bit

eval-lora:        ## дообученная модель
	python -m t2s.evaluate --name lora --backend hf --model $(MODEL) --adapter $(ADAPTER) --load-in-4bit

eval-api:         ## API-модель: make eval-api API_MODEL=... PRICE_IN=... PRICE_OUT=...
	python -m t2s.evaluate --name api --backend openai --model $(API_MODEL) \
		--price-in $(PRICE_IN) --price-out $(PRICE_OUT)

report:           ## таблица results/RESULTS.md и график
	python -m t2s.report --results results

compare:          ## какие задания дообучение исправило / сломало
	python -m t2s.compare results/base_predictions.jsonl results/lora_predictions.jsonl

test:
	pytest

test-slow:
	pytest -m slow

lint:
	ruff check src tests app.py
