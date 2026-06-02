"""
Quotes Web Scraper & Inverted Index Search Tool
================================================
Website: https://quotes.toscrape.com/
Politeness window: 6 seconds between requests

Commands:
  build  - Crawl the website, build the inverted index, and save to disk
  load   - Load a previously built index from disk
  print  - Print the inverted index entry for a specific word
  find   - Find all pages containing one or more words
"""

import json
import time
import re
import sys
import os
from collections import defaultdict
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found. Install it with: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: 'beautifulsoup4' library not found. Install it with: pip install beautifulsoup4")
    sys.exit(1)

BASE_URL        = "https://quotes.toscrape.com"
INDEX_FILE      = "inverted_index.json"
POLITENESS_SEC  = 6 

def tokenise(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def fetch_page(url: str, session: requests.Session) -> Optional[BeautifulSoup]:
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as exc:
        print(f"  [WARNING] Could not fetch {url}: {exc}")
        return None

# Pull the meaningful visible text from a quotes page. Focuses on quote text, author names, and tag words.
def extract_text(soup: BeautifulSoup) -> str:
    parts = []
    for quote_div in soup.select("div.quote"):
        span = quote_div.select_one("span.text")
        if span:
            parts.append(span.get_text())

        author = quote_div.select_one("small.author")
        if author:
            parts.append(author.get_text())

        for tag in quote_div.select("a.tag"):
            parts.append(tag.get_text())

    if not parts:
        parts.append(soup.get_text())

    return " ".join(parts)

# Return a word-frequency dictionary for the visible text on this page.
def build_page_index(url: str, soup: BeautifulSoup) -> dict[str, int]:
    text   = extract_text(soup)
    tokens = tokenise(text)
    freq: dict[str, int] = defaultdict(int)
    for token in tokens:
        freq[token] += 1
    return dict(freq)

# Crawl all paginated pages of quotes.toscrape.com, build and return the inverted index.
def crawl_and_build() -> dict:
    inverted_index: dict[str, dict[str, int]] = defaultdict(dict)
    session        = requests.Session()
    session.headers.update({"User-Agent": "QuoteIndexBot/1.0 (educational scraper)"})

    visited:  set[str] = set()
    to_visit: list[str] = [BASE_URL + "/"]
    page_count = 0

    print(f"Starting crawl of {BASE_URL}")

    while to_visit:
        url = to_visit.pop(0)
        if not url.endswith("/"):
            url += "/"

        if url in visited:
            continue
        visited.add(url)

        print(f"  Fetching [{page_count + 1}]: {url}")
        soup = fetch_page(url, session)

        if soup is None:
            continue

        page_count += 1

        freq = build_page_index(url, soup)
        for word, count in freq.items():
            inverted_index[word][url] = count

        next_btn = soup.select_one("li.next > a")
        if next_btn and next_btn.get("href"):
            next_url = BASE_URL + next_btn["href"]
            if next_url not in visited:
                to_visit.append(next_url)

        if to_visit:
            print(f"    Waiting {POLITENESS_SEC}s …")
            time.sleep(POLITENESS_SEC)

    print(f"\nCrawl complete. Pages visited: {page_count}")
    return dict(inverted_index)

def save_index(index: dict, filepath: str = INDEX_FILE) -> None:
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2, ensure_ascii=False)
    print(f"Index saved to '{filepath}' ({os.path.getsize(filepath):,} bytes).")


def load_index(filepath: str = INDEX_FILE) -> Optional[dict]:
    if not os.path.exists(filepath):
        print(f"Error: Index file '{filepath}' not found.")
        print("Run the 'build' command first to create the index.")
        return None
    with open(filepath, "r", encoding="utf-8") as fh:
        index = json.load(fh)
    print(f"Index loaded from '{filepath}'. "
          f"Unique words: {len(index):,}.")
    return index

# Commands
# build — crawl the site, create the index, and save it.
def cmd_build() -> dict:
    index = crawl_and_build()
    save_index(index)
    return index

# load — load a previously saved index from disk.
def cmd_load() -> Optional[dict]:
    return load_index()


# print <word> — display the inverted index entry for that word.
def cmd_print(index: Optional[dict], word: str) -> None:
    if index is None:
        print("No index loaded. Use 'load' or 'build' first.")
        return

    word = word.strip().lower()
    if not word:
        print("Usage: print <word>")
        return

    entry = index.get(word)
    if entry is None:
        print(f"Word '{word}' not found in the index.")
        return

    print(f"\nInverted index for '{word}':")
    for url, freq in sorted(entry.items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {url}  →  {freq} occurrence(s)")
    print(f"\nTotal pages containing '{word}': {len(entry)}\n")

"""
    find <word> [word2 …] — list all pages that contain ALL query words.

    - Single word  → union of pages for that word.
    - Multiple words → intersection (pages containing every word).
    """
def cmd_find(index: Optional[dict], query: str) -> None:
    if index is None:
        print("No index loaded. Use 'load' or 'build' first.")
        return

    words = [w.lower() for w in query.split() if w]
    if not words:
        print("Usage: find <word> [word2 …]")
        return

    page_sets = []
    missing   = []
    for word in words:
        if word in index:
            page_sets.append(set(index[word].keys()))
        else:
            missing.append(word)

    if missing:
        print(f"Word(s) not found in index: {', '.join(missing)}")
        if len(missing) == len(words):
            return 

    if not page_sets:
        print("No matching pages found.")
        return

    result_pages = page_sets[0]
    for s in page_sets[1:]:
        result_pages = result_pages & s

    query_display = " + ".join(f"'{w}'" for w in words)
    if not result_pages:
        print(f"\nNo pages found containing all of: {query_display}\n")
        return

    print(f"\nPages containing {query_display}:")
    for page in sorted(result_pages):
        freq_info = ", ".join(
            f"'{w}': {index[w].get(page, 0)}×" for w in words if w in index
        )
        print(f"  {page}  [{freq_info}]")
    print(f"\nTotal: {len(result_pages)} page(s)\n")

HELP_TEXT = """
Commands:
  build              Crawl the website, build the inverted index, and save it.
  load               Load a previously built index from disk.
  print <word>       Print the inverted index entry for <word>.
  find <word(s)>     Find pages containing all of the given word(s).
  help               Show this help message.
  quit / exit        Exit the tool.
"""
def run_repl() -> None:
    print("=" * 60)
    print("  Quotes Search Tool — https://quotes.toscrape.com")
    print("=" * 60)
    print(HELP_TEXT)

    index: Optional[dict] = None

    while True:
        try:
            raw = input("search> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not raw:
            continue

        parts   = raw.split(maxsplit=1)
        command = parts[0].lower()
        args    = parts[1] if len(parts) > 1 else ""

        if command == "build":
            index = cmd_build()

        elif command == "load":
            index = cmd_load()

        elif command == "print":
            if not args:
                print("Usage: print <word>")
            else:
                cmd_print(index, args.strip())

        elif command == "find":
            if not args:
                print("Usage: find <word> [word2 …]")
            else:
                cmd_find(index, args.strip())

        elif command in ("help", "?"):
            print(HELP_TEXT)

        elif command in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        else:
            print(f"Unknown command: '{command}'. Type 'help' for a list of commands.")

# Pass the command and args directly on the command line.
def run_single_command(argv: list[str]) -> None:
    command = argv[1].lower()
    args    = " ".join(argv[2:])

    index: Optional[dict] = None

    if command == "build":
        cmd_build()

    elif command == "load":
        index = cmd_load()

    elif command == "print":
        index = load_index()
        if index:
            cmd_print(index, args)

    elif command == "find":
        index = load_index()
        if index:
            cmd_find(index, args)

    elif command in ("help", "--help", "-h"):
        print(HELP_TEXT)

    else:
        print(f"Unknown command: '{command}'.")
        print(HELP_TEXT)

#Entry point
if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_single_command(sys.argv)
    else:
        run_repl()