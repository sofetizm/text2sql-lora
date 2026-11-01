from __future__ import annotations

SYSTEM_PROMPT = (
    "You are an expert SQL assistant. Given a SQLite database schema and a question, "
    "write one SQLite query that answers the question. "
    "Return only the SQL query, without explanations."
)


def build_user_message(schema: str, question: str) -> str:
    return f"### Schema\n{schema.strip()}\n\n### Question\n{question.strip()}"


def build_messages(schema: str, question: str, answer: str | None = None) -> list[dict]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(schema, question)},
    ]
    if answer is not None:
        messages.append({"role": "assistant", "content": answer.strip()})
    return messages
