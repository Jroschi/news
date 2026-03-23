from __future__ import annotations

from bs4 import BeautifulSoup


class ArticleExtractor:
    NOISE_SELECTORS = [
        "script",
        "style",
        "noscript",
        "header",
        "footer",
        "nav",
        "aside",
        ".cookie",
        ".advertisement",
        ".ads",
        ".promo",
    ]

    def __init__(self, max_characters: int = 12000) -> None:
        self.max_characters = max_characters

    def extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for selector in self.NOISE_SELECTORS:
            for tag in soup.select(selector):
                tag.decompose()

        containers = [soup.find(tag) for tag in ("article", "main")]
        containers.extend(soup.select("[role='main'], .article, .article-body, .content, .post-content"))

        text = self._from_containers(containers)
        if not text:
            text = self._paragraph_density_fallback(soup)
        return text[: self.max_characters].strip()

    @staticmethod
    def _from_containers(containers: list) -> str:
        for container in containers:
            if container is None:
                continue
            paragraphs = [p.get_text(" ", strip=True) for p in container.find_all("p")]
            paragraphs = [p for p in paragraphs if len(p.split()) >= 8]
            if paragraphs:
                return "\n\n".join(paragraphs)
        return ""

    @staticmethod
    def _paragraph_density_fallback(soup: BeautifulSoup) -> str:
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        dense = [paragraph for paragraph in paragraphs if len(paragraph.split()) >= 12]
        if dense:
            return "\n\n".join(dense)
        return soup.get_text(" ", strip=True)
