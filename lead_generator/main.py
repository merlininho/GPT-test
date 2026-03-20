"""Ponto de entrada do MicroSaaS local para geração de leads qualificados."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd

from ai_analysis import AILeadAnalyzer
from enrich import LeadEnricher
from scorer import calculate_score
from scraper import GoogleMapsScraper
from utils import log


OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "leads_clinicas.csv"


def collect_user_inputs() -> tuple[str, str]:
    """Solicita ao usuário os filtros de busca."""
    city = input("Informe a cidade para prospecção: ").strip()
    clinic_type = input(
        "Informe o tipo de clínica (ex.: clínica odontológica, clínica estética, clínica médica): "
    ).strip()
    return city, clinic_type


def build_dataframe(leads: List[Dict[str, object]]) -> pd.DataFrame:
    """Converte os leads processados em DataFrame final ordenado por score."""
    rows = []
    for lead in leads:
        rows.append(
            {
                "Nome": lead.get("nome", ""),
                "Telefone": lead.get("telefone", ""),
                "Website": lead.get("website", ""),
                "Avaliações": lead.get("avaliacoes", 0),
                "Nota": lead.get("nota", 0.0),
                "Score": lead.get("score", 0),
                "Profissionalismo": lead.get("nivel_profissionalismo", "Não analisado"),
                "Complexidade": lead.get("complexidade_operacional", "Não analisado"),
                "Dor Financeira": lead.get("probabilidade_dor_financeira", "Não analisado"),
                "Resumo": lead.get("resumo_curto", ""),
            }
        )

    dataframe = pd.DataFrame(rows)
    if not dataframe.empty:
        dataframe = dataframe.sort_values(by="Score", ascending=False)
    return dataframe


def main() -> None:
    """Executa o pipeline completo de scraping, enriquecimento, score e IA."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    city, clinic_type = collect_user_inputs()

    scraper = GoogleMapsScraper(headless=True, max_results=15)
    enricher = LeadEnricher()
    analyzer = AILeadAnalyzer()

    raw_leads = scraper.scrape(city=city, clinic_type=clinic_type)
    if not raw_leads:
        log("Nenhum lead foi coletado. Gerando CSV vazio para referência.", level="warning")

    enriched_leads = enricher.enrich_leads(raw_leads)

    final_leads: List[Dict[str, object]] = []
    for lead in enriched_leads:
        lead["score"] = calculate_score(lead)

        if lead.get("descricao_site"):
            ai_result = analyzer.analyze(
                company_name=str(lead.get("nome", "")),
                site_description=str(lead.get("descricao_site", "")),
            )
            lead.update(ai_result)
        else:
            lead.update(
                {
                    "nivel_profissionalismo": "Não analisado",
                    "complexidade_operacional": "Não analisado",
                    "probabilidade_dor_financeira": "Não analisado",
                    "resumo_curto": "Sem descrição de site disponível.",
                }
            )

        final_leads.append(lead)

    dataframe = build_dataframe(final_leads)
    dataframe.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    log(f"Arquivo final salvo em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
