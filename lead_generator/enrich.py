"""Módulo de enriquecimento de dados coletados via scraping."""

from __future__ import annotations

from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from utils import clean_text, log, truncate_text


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )
}


class LeadEnricher:
    """Enriquece leads com conteúdo do website e presença simulada de Instagram."""

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout

    def enrich_leads(self, leads: List[Dict[str, object]]) -> List[Dict[str, object]]:
        """Aplica enriquecimento individual a todos os leads."""
        enriched: List[Dict[str, object]] = []
        for lead in leads:
            enriched.append(self.enrich_single_lead(lead))
        return enriched

    def enrich_single_lead(self, lead: Dict[str, object]) -> Dict[str, object]:
        """Enriquece um lead sem interromper o pipeline em caso de erro."""
        lead = dict(lead)
        website = clean_text(lead.get("website"))

        lead["possui_site"] = bool(website)
        lead["descricao_site"] = ""
        lead["possui_instagram"] = False

        if not website:
            return lead

        try:
            response = requests.get(website, headers=HEADERS, timeout=self.timeout)
            response.raise_for_status()
            html = response.text
            lead["descricao_site"] = self._extract_main_text(html)
            lead["possui_instagram"] = self._find_instagram(html)
        except Exception as exc:  # noqa: BLE001
            log(f"Falha ao enriquecer site {website}: {exc}", level="warning")

        return lead

    def _extract_main_text(self, html: str) -> str:
        """Extrai o texto principal do HTML para servir de contexto ao score e IA."""
        soup = BeautifulSoup(html, "html.parser")

        for element in soup(["script", "style", "noscript", "svg"]):
            element.decompose()

        candidates = [
            soup.find("main"),
            soup.find("article"),
            soup.find("body"),
        ]
        container = next((candidate for candidate in candidates if candidate), soup)
        text = clean_text(container.get_text(" ", strip=True))
        return truncate_text(text, limit=2000)

    def _find_instagram(self, html: str) -> bool:
        """Simula descoberta de Instagram procurando links e menções no HTML."""
        lowered_html = html.lower()
        instagram_signals = ["instagram.com", "@instagram", "instagram"]
        return any(signal in lowered_html for signal in instagram_signals)
