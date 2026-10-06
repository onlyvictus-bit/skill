#!/usr/bin/env python3
"""Optional exact token accounting and complete batching for Claude Mon."""
from __future__ import annotations

from typing import Iterable


class BudgetError(RuntimeError):
    pass


def _tiktoken():
    try:
        import tiktoken  # type: ignore
    except ImportError as exc:
        raise BudgetError("tiktoken is not installed; install only with explicit authorization or provide counts from the active runtime") from exc
    return tiktoken


def resolve_encoding(model: str | None = None, explicit_encoding: str | None = None):
    tk = _tiktoken()
    if explicit_encoding:
        return tk.get_encoding(explicit_encoding)
    if model:
        try:
            return tk.encoding_for_model(model)
        except KeyError as exc:
            raise BudgetError(f"unknown model tokenizer mapping: {model}; provide explicit_encoding") from exc
    raise BudgetError("model or explicit_encoding is required")


def count_tokens(text: str, model: str | None = None, explicit_encoding: str | None = None) -> int:
    enc = resolve_encoding(model=model, explicit_encoding=explicit_encoding)
    return len(enc.encode(text))


def schedule_batches(
    items: Iterable[tuple[str, int]],
    *,
    context_limit: int,
    reserved_output_tokens: int,
    fixed_overhead_tokens: int = 0,
) -> list[list[str]]:
    usable = context_limit - reserved_output_tokens - fixed_overhead_tokens
    if context_limit <= 0 or reserved_output_tokens < 0 or fixed_overhead_tokens < 0 or usable <= 0:
        raise BudgetError("invalid token budget")
    batches: list[list[str]] = []
    current: list[str] = []
    used = 0
    for item_id, count in items:
        if count < 0:
            raise BudgetError(f"negative token count for {item_id}")
        if count > usable:
            raise BudgetError(f"required item {item_id} needs {count} tokens but usable budget is {usable}; split it instead of truncating")
        if current and used + count > usable:
            batches.append(current)
            current = []
            used = 0
        current.append(item_id)
        used += count
    if current:
        batches.append(current)
    return batches
