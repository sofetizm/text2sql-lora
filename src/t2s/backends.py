from __future__ import annotations

import os
import time
from dataclasses import dataclass, field


@dataclass
class Generation:
    text: str
    latency_s: float
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    extra: dict = field(default_factory=dict)


class Backend:
    name = "base"

    def generate(self, batch: list[list[dict]]) -> list[Generation]:
        raise NotImplementedError

    def describe(self) -> dict:
        return {"backend": self.name}


class HFBackend(Backend):

    name = "hf"

    def __init__(self, model_name: str, adapter: str | None = None, load_in_4bit: bool = False,
                 max_new_tokens: int = 256):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        self.torch = torch
        self.model_name, self.adapter = model_name, adapter
        self.max_new_tokens = max_new_tokens
        self.tokenizer = AutoTokenizer.from_pretrained(adapter or model_name)
        self.tokenizer.padding_side = "left"  # для батчевой генерации у decoder-only
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        cuda = torch.cuda.is_available()
        dtype = (torch.bfloat16 if cuda and torch.cuda.is_bf16_supported()
                 else torch.float16 if cuda else torch.float32)
        kwargs: dict = {"dtype": dtype}
        if cuda:
            kwargs["device_map"] = {"": 0}
        self.quantized = load_in_4bit and cuda
        if self.quantized:
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=dtype)
        model = AutoModelForCausalLM.from_pretrained(model_name, **kwargs)
        if adapter:
            from peft import PeftModel

            model = PeftModel.from_pretrained(model, adapter)
            if not self.quantized:
                model = model.merge_and_unload()  # быстрее инференс
        self.model = model.eval()
        self.device = next(self.model.parameters()).device

    def generate(self, batch: list[list[dict]]) -> list[Generation]:
        torch = self.torch
        prompts = [self.tokenizer.apply_chat_template(m, tokenize=False,
                                                      add_generation_prompt=True) for m in batch]
        enc = self.tokenizer(prompts, return_tensors="pt", padding=True,
                             add_special_tokens=False).to(self.device)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        started = time.perf_counter()
        with torch.inference_mode():
            out = self.model.generate(**enc, max_new_tokens=self.max_new_tokens, do_sample=False,
                                      pad_token_id=self.tokenizer.pad_token_id)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        elapsed = time.perf_counter() - started

        new_tokens = out[:, enc["input_ids"].shape[1]:]
        results = []
        for i, row in enumerate(new_tokens):
            n_out = int((row != self.tokenizer.pad_token_id).sum())
            results.append(Generation(
                text=self.tokenizer.decode(row, skip_special_tokens=True),
                latency_s=elapsed / len(batch),  # время батча делится поровну
                input_tokens=int(enc["attention_mask"][i].sum()),
                output_tokens=n_out))
        return results

    def describe(self) -> dict:
        return {"backend": self.name, "model": self.model_name, "adapter": self.adapter,
                "quantized_4bit": self.quantized}


class OpenAIBackend(Backend):

    name = "openai"

    def __init__(self, model: str, price_in: float = 0.0, price_out: float = 0.0,
                 max_tokens: int = 256, base_url: str | None = None, rpm: float = 0.0,
                 reasoning_effort: str | None = None, client=None):
        self.model, self.price_in, self.price_out = model, price_in, price_out
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self.min_interval = 60.0 / rpm if rpm > 0 else 0.0
        self._last_call = 0.0
        if client is None:
            from openai import OpenAI

            client = OpenAI(base_url=base_url or os.environ.get("OPENAI_BASE_URL"), max_retries=8)
        self.client = client

    def _wait_for_slot(self) -> None:
        delay = self._last_call + self.min_interval - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        self._last_call = time.monotonic()

    def _one(self, messages: list[dict]) -> Generation:
        kwargs = {"model": self.model, "messages": messages, "temperature": 0,
                  "max_tokens": self.max_tokens}
        if self.reasoning_effort:
            kwargs["reasoning_effort"] = self.reasoning_effort
        self._wait_for_slot()
        started = time.perf_counter()
        resp = self.client.chat.completions.create(**kwargs)
        elapsed = time.perf_counter() - started
        usage = resp.usage
        n_in = usage.prompt_tokens if usage else 0
        n_out = usage.completion_tokens if usage else 0
        return Generation(
            text=resp.choices[0].message.content or "", latency_s=elapsed,
            input_tokens=n_in, output_tokens=n_out,
            cost_usd=(n_in * self.price_in + n_out * self.price_out) / 1_000_000)

    def generate(self, batch: list[list[dict]]) -> list[Generation]:
        results = []
        for messages in batch:
            try:
                results.append(self._one(messages))
            except Exception as e:
                print(f"  [!] ошибка API: {type(e).__name__}: {str(e)[:200]}", flush=True)
                results.append(Generation(text="", latency_s=0.0,
                                          extra={"error": f"{type(e).__name__}: {e}"}))
        return results

    def describe(self) -> dict:
        return {"backend": self.name, "model": self.model,
                "reasoning_effort": self.reasoning_effort,
                "price_in_per_1m": self.price_in, "price_out_per_1m": self.price_out}


class OracleBackend(Backend):

    name = "oracle"

    def __init__(self, answers: dict[str, str]):
        self.answers = answers

    def generate(self, batch: list[list[dict]]) -> list[Generation]:
        return [Generation(text=f"```sql\n{self.answers[m[-1]['content']]};\n```", latency_s=0.0)
                for m in batch]
