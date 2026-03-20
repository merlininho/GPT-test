"""Funções utilitárias para logging, limpeza de texto e tratamento seguro de erros."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Callable, Optional


LOG_LEVELS = {"info": "INFO", "warning": "WARN", "error": "ERROR"}


def log(message: str, level: str = "info") -> None:
    """Exibe logs simples com timestamp no terminal."""
    normalized_level = LOG_LEVELS.get(level.lower(), "INFO")
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{normalized_level}] {message}")


def clean_text(value: Any) -> str:
    """Normaliza espaços, remove quebras de linha e converte nulos para string vazia."""
    if value is None:
        return ""

    text = str(value)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate_text(value: str, limit: int = 1500) -> str:
    """Limita textos longos para evitar prompts gigantes e arquivos poluídos."""
    text = clean_text(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


def safe_int(value: Any, default: int = 0) -> int:
    """Converte valores numéricos em inteiro, ignorando ruídos de scraping."""
    if value is None:
        return default

    if isinstance(value, int):
        return value

    digits = re.findall(r"\d+", str(value).replace(".", ""))
    if not digits:
        return default
    return int("".join(digits))


def safe_float(value: Any, default: float = 0.0) -> float:
    """Converte strings em ponto flutuante de forma tolerante a falhas."""
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return float(value)

    normalized = str(value).replace(",", ".")
    match = re.search(r"\d+(?:\.\d+)?", normalized)
    if not match:
        return default
    return float(match.group())


def run_safely(
    operation: Callable[..., Any],
    *args: Any,
    fallback: Optional[Any] = None,
    error_message: str = "Operação falhou.",
    **kwargs: Any,
) -> Any:
    """Executa uma operação protegida, registra erro e retorna fallback em caso de exceção."""
    try:
        return operation(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - fallback proposital em fluxo resiliente
        log(f"{error_message} Erro: {exc}", level="error")
        return fallback
