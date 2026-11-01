"""Крошечная случайная модель Qwen2 + токенизатор с ChatML-шаблоном.

Нужна для smoke-теста обучения на CPU без скачивания весов: проверяем, что
весь пайплайн (токенизация с маскированием, LoRA, сохранение адаптера,
загрузка адаптера в инференс) работает, а не качество.
"""
from pathlib import Path

CHATML = (
    "{% for message in messages %}"
    "{{ '<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n' }}"
    "{% endfor %}"
    "{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}"
)


def make_tiny_model(out_dir: str | Path) -> Path:
    from tokenizers import Tokenizer, models, pre_tokenizers, trainers
    from transformers import PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM

    out = Path(out_dir)
    specials = ["<|endoftext|>", "<|im_start|>", "<|im_end|>"]
    tok = Tokenizer(models.BPE())
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    corpus = ["SELECT name FROM t WHERE id = 1", "CREATE TABLE t (id INTEGER, name TEXT)",
              "### Schema ### Question You are an expert SQL assistant. Return only the SQL.",
              "system user assistant How many what is the count average"] * 50
    tok.train_from_iterator(corpus, trainers.BpeTrainer(
        vocab_size=400, special_tokens=specials,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
    from tokenizers import decoders
    tok.decoder = decoders.ByteLevel()

    hf_tok = PreTrainedTokenizerFast(tokenizer_object=tok, eos_token="<|im_end|>",
                                     pad_token="<|endoftext|>")
    hf_tok.chat_template = CHATML
    hf_tok.save_pretrained(out)

    config = Qwen2Config(vocab_size=len(hf_tok), hidden_size=32, intermediate_size=64,
                         num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2,
                         max_position_embeddings=1024, eos_token_id=hf_tok.eos_token_id,
                         pad_token_id=hf_tok.pad_token_id, tie_word_embeddings=True)
    Qwen2ForCausalLM(config).save_pretrained(out)
    return out
