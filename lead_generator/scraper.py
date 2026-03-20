"""Scraping de clínicas no Google Maps usando Playwright."""

from __future__ import annotations

import time
from typing import Dict, List
from urllib.parse import quote_plus

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from utils import clean_text, log, safe_float, safe_int


MAPS_BASE_URL = "https://www.google.com/maps/search/"


class GoogleMapsScraper:
    """Responsável por buscar empresas no Google Maps e extrair campos principais."""

    def __init__(self, headless: bool = True, max_results: int = 20) -> None:
        self.headless = headless
        self.max_results = max_results

    def scrape(self, city: str, clinic_type: str) -> List[Dict[str, object]]:
        """Executa o scraping para uma cidade e tipo de clínica."""
        search_term = f"{clinic_type} em {city}"
        search_url = f"{MAPS_BASE_URL}{quote_plus(search_term)}"
        log(f"Iniciando scraping para: {search_term}")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            page = browser.new_page(viewport={"width": 1440, "height": 1080})
            results: List[Dict[str, object]] = []

            try:
                page.goto(search_url, timeout=90000, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)
                self._accept_cookies_if_present(page)
                self._scroll_results(page)
                cards = page.locator('a[href*="/place/"]')
                total_cards = min(cards.count(), self.max_results)
                log(f"Total de cards encontrados: {total_cards}")

                for index in range(total_cards):
                    try:
                        card = cards.nth(index)
                        card.click(timeout=10000)
                        page.wait_for_timeout(3000)
                        result = self._extract_place_data(page)
                        if result.get("nome"):
                            results.append(result)
                            log(f"Lead coletado: {result['nome']}")
                    except Exception as exc:  # noqa: BLE001
                        log(f"Falha ao extrair card {index + 1}: {exc}", level="warning")
                        continue
            except Exception as exc:  # noqa: BLE001
                log(f"Scraping do Google Maps falhou: {exc}", level="error")
            finally:
                browser.close()

        return results

    def _accept_cookies_if_present(self, page) -> None:
        """Aceita banners de cookies, quando exibidos."""
        selectors = [
            'button:has-text("Aceitar tudo")',
            'button:has-text("Accept all")',
            'button:has-text("I agree")',
        ]
        for selector in selectors:
            try:
                button = page.locator(selector)
                if button.count() > 0:
                    button.first.click(timeout=3000)
                    page.wait_for_timeout(1000)
                    return
            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue

    def _scroll_results(self, page) -> None:
        """Rola a lista de resultados para carregar mais estabelecimentos."""
        scrollable = page.locator('div[role="feed"]')
        if scrollable.count() == 0:
            log("Container de resultados não encontrado; seguindo com itens visíveis.", level="warning")
            return

        panel = scrollable.first
        for _ in range(6):
            panel.hover()
            page.mouse.wheel(0, 6000)
            time.sleep(1)

    def _extract_place_data(self, page) -> Dict[str, object]:
        """Extrai dados estruturados da ficha do local aberto."""
        name = self._text_or_empty(page, 'h1')
        address = self._text_or_empty(page, 'button[data-item-id="address"]')
        website = self._attribute_or_empty(page, 'a[data-item-id="authority"]', 'href')
        phone = self._text_or_empty(page, 'button[data-item-id^="phone:"]')
        rating = self._text_or_empty(page, 'div[role="main"] span[aria-hidden="true"]')
        reviews_text = self._text_or_empty(page, 'button[jsaction*="pane.rating.moreReviews"]')

        return {
            "nome": clean_text(name),
            "avaliacoes": safe_int(reviews_text),
            "nota": safe_float(rating),
            "telefone": clean_text(phone),
            "website": clean_text(website),
            "endereco": clean_text(address),
        }

    @staticmethod
    def _text_or_empty(page, selector: str) -> str:
        locator = page.locator(selector)
        if locator.count() == 0:
            return ""
        try:
            return clean_text(locator.first.inner_text(timeout=3000))
        except Exception:
            return ""

    @staticmethod
    def _attribute_or_empty(page, selector: str, attribute: str) -> str:
        locator = page.locator(selector)
        if locator.count() == 0:
            return ""
        try:
            return clean_text(locator.first.get_attribute(attribute, timeout=3000) or "")
        except Exception:
            return ""
