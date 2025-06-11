"""
danbooru_scraper.py
Busca as tags mais frequentes de um personagem no Danbooru.

Uso:
    python danbooru_scraper.py <character_tag>
"""

import math
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

# --- Configurações ---------------------------------------------------------

UA = "Mozilla/5.0 (compatible; TagScraper/1.0; +https://github.com/)"
MAX_WORKERS = 8          # limite de threads
TIMEOUT = 10             # segundos
RETRIES = 3              # tentativas de download por página

# --- Sessão HTTP com retries ----------------------------------------------

session = requests.Session()
session.headers["User-Agent"] = UA
adapter = requests.adapters.HTTPAdapter(
    pool_maxsize=MAX_WORKERS, max_retries=RETRIES
)
session.mount("https://", adapter)

# --- Etapa 1 – baixar páginas ---------------------------------------------

def fetch(url: str) -> str:
    """Faz download de uma URL com pequenas retentativas."""
    for _ in range(RETRIES):
        try:
            r = session.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            return r.text
        except requests.exceptions.RequestException:
            time.sleep(1)
    return ""

def scrape_page(tag: str, page: int) -> list[str]:
    """Extrai o conteúdo de data‑tags de uma página."""
    html = fetch(f"https://danbooru.donmai.us/posts?page={page}&tags={tag}")
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")      # lxml é bem mais rápido
    return [art["data-tags"] for art in soup.select(
        "div.posts-container.gap-2 > article"
    )]

def scrape_booru(tag: str, num_pages: int = 3) -> list[str]:
    """Busca várias páginas em paralelo e devolve a lista de strings de tags."""
    workers = min(MAX_WORKERS, num_pages)
    tags: list[str] = []
    with ThreadPoolExecutor(max_workers=workers) as exe:
        futures = {exe.submit(scrape_page, tag, p): p for p in range(1, num_pages + 1)}
        for f in as_completed(futures):
            tags.extend(f.result())
    return tags

# --- Etapa 2 – filtrar e escolher tags ------------------------------------

KEYWORDS = {
    "bangs", "belt", "bow", "braid", "choker", "earring", "ears", "eyes",
    "eyeshadow", "hair", "hair ornament", "hairband", "hat", "headband",
    "headphones", "headwear", "horns", "mask", "necklace", "ponytail", "tail",
    "thighhigh", "wings",
}
EXCLUDED_RE = re.compile(r"^(?!1)\d+(girl|boy)s?$")   # permite 1girl/1boy

def process_tags(tags_raw: list[str], character_tag: str) -> str:
    """Transforma tags brutas em uma string final, mantendo as mais relevantes."""
    if not tags_raw:
        return character_tag

    # achata lista e conta frequência
    all_tags = [t for raw in tags_raw for t in raw.split()]
    counter = Counter(all_tags)

    half = math.ceil(len(tags_raw) / 2)
    frequent = {t: c for t, c in counter.items() if c >= half}

    # gênero se aparecer em ≥ metade das imagens
    gender_tag = next((g for g in ("1girl", "1boy") if g in frequent), None)

    # tags físicas/visuais mais relevantes
    related = sorted(
        (t for t in frequent if any(k in t for k in KEYWORDS)),
        key=lambda t: frequent[t],
        reverse=True,
    )[:8]

    # mais duas genéricas, respeitando exclusões
    additional = []
    for t, _ in counter.most_common():
        if t in related or t == character_tag or EXCLUDED_RE.match(t):
            continue
        additional.append(t)
        if len(additional) == 2:
            break

    # monta lista final sem duplicatas, mantendo ordem
    final = [character_tag]
    if gender_tag:
        final.append(gender_tag)
    final.extend(related)
    final.extend(additional)
    return ", ".join(dict.fromkeys(final))   # dict mantém primeira ocorrência

# --- Interface de alto nível ----------------------------------------------

def get_character_tags(character_tag: str, pages: int = 3) -> str:
    raw = scrape_booru(character_tag, pages)
    return process_tags(raw, character_tag)

# --- Execução direta -------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python danbooru_scraper.py <character_tag>")
        sys.exit(1)

    print(get_character_tags(sys.argv[1]))
