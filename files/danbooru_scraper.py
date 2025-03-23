import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

def scrape_page(tag, page):
    url = f"https://danbooru.donmai.us/posts?page={page}&tags={tag}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.select('div.posts-container.gap-2 > article')
    return [article['data-tags'] for article in articles]

def scrape_booru(tag, num_pages=3):
    tags_list = []
    with ThreadPoolExecutor(max_workers=num_pages) as executor:
        future_to_page = {executor.submit(scrape_page, tag, page): page for page in range(1, num_pages + 1)}
        for future in as_completed(future_to_page):
            try:
                page_tags = future.result()
                tags_list.extend(page_tags)
            except Exception:
                pass
    return tags_list

def process_tags(tags_list, character_tag):
    if not tags_list:
        return f"1girl, {character_tag}"
    
    all_tags = []
    for tags in tags_list:
        all_tags.extend(tags.split())
    
    tag_counter = Counter(all_tags)
    num_images = len(tags_list)
    threshold = math.ceil(num_images / 2)
    
    frequent_tags = {tag: count for tag, count in tag_counter.items() if count >= threshold}
    
    keywords = [
        "bangs", "belt", "bow", "braid", "choker", "earring", "ears", "eyes", "eyeshadow",
        "hair", "hair ornament", "hairband", "hat", "headband", "headphones", "headwear",
        "horns", "mask", "necklace", "ponytail", "tail", "thighhigh", "wings"
    ]
    
    related_tags = [tag for tag in frequent_tags if any(keyword in tag for keyword in keywords)]
    related_tags_sorted = sorted(related_tags, key=lambda x: tag_counter[x], reverse=True)
    selected_tags = related_tags_sorted[:8]
    
    excluded_pattern = re.compile(r'^\d+(girl|boy)s?$')
    additional_tags = []
    for tag in sorted(frequent_tags, key=lambda x: tag_counter[x], reverse=True):
        if (tag not in selected_tags and 
            not excluded_pattern.match(tag) and 
            tag != character_tag):
            additional_tags.append(tag)
            if len(additional_tags) == 2:
                break
    
    final_tags = ["1girl", character_tag] + selected_tags + additional_tags
    return ", ".join(final_tags)

def get_character_tags(character_tag):
    """Função principal que retorna os tags do personagem como uma string."""
    tags_list = scrape_booru(character_tag, num_pages=3)
    return process_tags(tags_list, character_tag)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python danbooru_scraper.py <character_tag>")
        sys.exit(1)
    
    character_tag = sys.argv[1]
    result = get_character_tags(character_tag)
    print(result)