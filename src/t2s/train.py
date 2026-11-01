from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path

import torch
import yaml
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    Trainer,
    TrainingArguments,
    set_seed,
)

from .data import read_jsonl
from .prompts import build_messages

IGNORE_INDEX = -100


def load_config(path: str, overrides: list[str]) -> dict:
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    for item in overrides:
        key, value = item.split("=", 1)
        node = cfg
        *parents, leaf = key.split(".")
        for p in parents:
            node = node.setdefault(p, {})
        node[leaf] = yaml.safe_load(value)
    return cfg


def tokenize_example(tokenizer, example: dict, max_len: int) -> dict | None:
    prompt = tokenizer.apply_chat_template(
        build_messages(example["schema"], example["question"]),
        tokenize=False, add_generation_prompt=True)
    full = tokenizer.apply_chat_template(
        build_messages(example["schema"], example["question"], example["sql"]),
        tokenize=False)
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    full_ids = tokenizer(full, add_special_tokens=False)["input_ids"]
    if len(full_ids) > max_len:
        return None
    labels = [IGNORE_INDEX] * len(prompt_ids) + full_ids[len(prompt_ids):]
    return {"input_ids": full_ids, "labels": labels}


class JsonlDataset(torch.utils.data.Dataset):
    def __init__(self, path: str, tokenizer, max_len: int):
        rows = [tokenize_example(tokenizer, r, max_len) for r in read_jsonl(path)]
        self.items = [r for r in rows if r is not None]
        self.skipped = len(rows) - len(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, i: int) -> dict:
        return self.items[i]


@dataclass
class PadCollator:
    pad_token_id: int

    def __call__(self, batch: list[dict]) -> dict:
        width = max(len(x["input_ids"]) for x in batch)
        ids, labels, mask = [], [], []
        for x in batch:
            pad = width - len(x["input_ids"])
            ids.append(x["input_ids"] + [self.pad_token_id] * pad)
            labels.append(x["labels"] + [IGNORE_INDEX] * pad)
            mask.append([1] * len(x["input_ids"]) + [0] * pad)
        return {"input_ids": torch.tensor(ids), "labels": torch.tensor(labels),
                "attention_mask": torch.tensor(mask)}


def precision_flags() -> dict:
    if not torch.cuda.is_available():
        return {"bf16": False, "fp16": False}
    if torch.cuda.is_bf16_supported():
        return {"bf16": True, "fp16": False}
    return {"bf16": False, "fp16": True}


def version_specific_args(t: dict) -> dict:
    """Аргументы, которые по-разному называются в transformers 4.x и 5.x."""
    import dataclasses

    fields = {f.name for f in dataclasses.fields(TrainingArguments)}
    ratio = t.get("warmup_ratio", 0.03)
    args = {"warmup_ratio": ratio} if "warmup_ratio" in fields else {"warmup_steps": ratio}
    if "group_by_length" in fields:
        args["group_by_length"] = True
    return args


def load_model(cfg: dict):
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    use_4bit = bool(cfg.get("load_in_4bit")) and torch.cuda.is_available()
    flags = precision_flags()
    compute_dtype = torch.bfloat16 if flags["bf16"] else torch.float16
    kwargs = {}
    if use_4bit:
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=compute_dtype)
        kwargs["device_map"] = {"": 0}
    elif torch.cuda.is_available():
        kwargs["dtype"] = compute_dtype
        kwargs["device_map"] = {"": 0}

    model = AutoModelForCausalLM.from_pretrained(cfg["model_name"], **kwargs)
    model.config.use_cache = False
    grad_ckpt = cfg["training"].get("gradient_checkpointing", False)
    if use_4bit:
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=grad_ckpt)
    elif grad_ckpt:
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()

    lora = cfg["lora"]
    model = get_peft_model(model, LoraConfig(
        r=lora["r"], lora_alpha=lora["alpha"], lora_dropout=lora["dropout"],
        target_modules=lora["target_modules"], bias="none", task_type="CAUSAL_LM"))
    return model, use_4bit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--set", nargs="*", default=[], metavar="KEY=VALUE",
                        help="переопределить поля конфига, например training.max_steps=50")
    args = parser.parse_args()
    cfg = load_config(args.config, args.set)
    set_seed(cfg.get("seed", 42))

    tokenizer = AutoTokenizer.from_pretrained(cfg["model_name"])
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    max_len = cfg.get("max_seq_length", 768)
    train_ds = JsonlDataset(cfg["train_file"], tokenizer, max_len)
    val_ds = JsonlDataset(cfg["val_file"], tokenizer, max_len) if cfg.get("val_file") else None
    print(f"train: {len(train_ds)} примеров (пропущено длинных: {train_ds.skipped})")

    model, use_4bit = load_model(cfg)
    trainable, total = model.get_nb_trainable_parameters()
    print(f"обучаемых параметров: {trainable:,} из {total:,} ({100 * trainable / total:.2f}%)")

    t = cfg["training"]
    out_dir = Path(cfg["output_dir"])
    has_eval = val_ds is not None and len(val_ds) > 0
    targs = TrainingArguments(
        output_dir=str(out_dir),
        num_train_epochs=t.get("num_train_epochs", 1),
        max_steps=t.get("max_steps", -1),
        per_device_train_batch_size=t["per_device_train_batch_size"],
        per_device_eval_batch_size=t.get("per_device_eval_batch_size",
                                         t["per_device_train_batch_size"]),
        gradient_accumulation_steps=t.get("gradient_accumulation_steps", 1),
        learning_rate=t["learning_rate"],
        lr_scheduler_type=t.get("lr_scheduler_type", "cosine"),
        weight_decay=t.get("weight_decay", 0.0),
        logging_steps=t.get("logging_steps", 20),
        eval_strategy="steps" if has_eval else "no",
        eval_steps=t.get("eval_steps", 200),
        save_strategy="steps",
        save_steps=t.get("save_steps", 200),
        save_total_limit=2,
        load_best_model_at_end=has_eval,
        metric_for_best_model="eval_loss" if has_eval else None,
        greater_is_better=False if has_eval else None,
        optim="paged_adamw_8bit" if use_4bit else "adamw_torch",
        report_to=t.get("report_to", "none"),
        seed=cfg.get("seed", 42),
        **precision_flags(),
        **version_specific_args(t),
    )
    trainer = Trainer(model=model, args=targs, train_dataset=train_ds,
                      eval_dataset=val_ds if has_eval else None,
                      data_collator=PadCollator(tokenizer.pad_token_id),
                      processing_class=tokenizer)

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    started = time.time()
    result = trainer.train()
    elapsed = time.time() - started

    adapter_dir = out_dir / "adapter"
    trainer.model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)

    meta = {
        "base_model": cfg["model_name"],
        "train_examples": len(train_ds),
        "trainable_params": trainable,
        "total_params": total,
        "train_loss": result.training_loss,
        "train_minutes": round(elapsed / 60, 1),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "peak_gpu_mem_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2)
        if torch.cuda.is_available() else None,
        "quantization": "4-bit nf4 (QLoRA)" if use_4bit else "none",
        "config": cfg,
    }
    if has_eval:
        meta["eval_loss"] = trainer.evaluate()["eval_loss"]
    (out_dir / "train_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(json.dumps({k: v for k, v in meta.items() if k != "config"}, indent=2,
                     ensure_ascii=False))
    print(f"адаптер сохранён: {adapter_dir}")

    if cfg.get("push_to_hub"):
        trainer.model.push_to_hub(cfg["push_to_hub"])
        tokenizer.push_to_hub(cfg["push_to_hub"])
        print(f"адаптер загружен на Hugging Face Hub: {cfg['push_to_hub']}")


if __name__ == "__main__":
    main()
