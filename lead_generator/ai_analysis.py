"""Análise de leads com OpenAI para classificar maturidade comercial/operacional."""

from __future__ import annotations

import json
import os
from typing import Dict, Optional

from openai import OpenAI

from utils import clean_text, log, truncate_text


SYSTEM_PROMPT = """
Você é um analista comercial B2B especializado em clínicas odontológicas, estéticas e médicas.
Avalie o nível de profissionalismo, complexidade operacional e probabilidade de dor financeira.
Responda SOMENTE em JSON válido com as chaves:
- nivel_profissionalismo
- complexidade_operacional
- probabilidade_dor_financeira
- resumo_curto
Use apenas os valores Alto/Médio/Baixo ou Alta/Média/Baixa conforme o campo.
""".strip()


class AILeadAnalyzer:
    """Encapsula chamadas ao modelo GPT via variável OPENAI_API_KEY."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        self.client: Optional[OpenAI] = OpenAI(api_key=api_key) if api_key else None
        self.model = model

    def analyze(self, company_name: str, site_description: str) -> Dict[str, str]:
        """Classifica um lead com IA; retorna fallback caso a API não esteja configurada."""
        fallback = {
            "nivel_profissionalismo": "Não analisado",
            "complexidade_operacional": "Não analisado",
            "probabilidade_dor_financeira": "Não analisado",
            "resumo_curto": "Análise indisponível.",
        }

        if not self.client:
            log("OPENAI_API_KEY não configurada; análise com IA será ignorada.", level="warning")
            return fallback

        prompt = self._build_prompt(company_name, site_description)

        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            content = response.output_text
            parsed = json.loads(content)
            return {
                "nivel_profissionalismo": parsed.get("nivel_profissionalismo", "Não analisado"),
                "complexidade_operacional": parsed.get("complexidade_operacional", "Não analisado"),
                "probabilidade_dor_financeira": parsed.get("probabilidade_dor_financeira", "Não analisado"),
                "resumo_curto": parsed.get("resumo_curto", "Análise indisponível."),
            }
        except Exception as exc:  # noqa: BLE001
            log(f"Falha na análise com IA para {company_name}: {exc}", level="warning")
            return fallback

    def _build_prompt(self, company_name: str, site_description: str) -> str:
        """Gera prompt contextualizado e compacto para o modelo."""
        description = truncate_text(clean_text(site_description), limit=1800)
        return (
            f"Empresa: {clean_text(company_name)}\n"
            f"Descrição do site: {description}\n\n"
            "Classifique a empresa considerando sinais de estrutura, marketing, variedade de serviços "
            "e possíveis dores administrativas/financeiras. O resumo deve ter apenas 1 linha."
        )
