# Quotes-Search-Tool
A command line web scraper and full text search engine built on top of quotes.toscrape.com. The tool crawls the site, builds an inverted index of every word across every page, and lets you search for quotes by keyword from the terminal.

## Features
* **Polite Crawler** – Respects a strict 6 second delay between requests to avoid overloading the host server.
* **Inverted Index** – Maps every unique word to the specific pages it appears on, alongside exact frequency counts.
* **Persistent Storage** – Saves to and loads from a local JSON file so you only ever have to crawl the website once.
* **Multi-Word Search** – Instantly find pages containing a single targeted keyword or the intersection of every word in a complex phrase.
* **Dual Execution Modes** – Run the tool via an interactive REPL terminal workspace or pass quick tasks directly using a single-command CLI mode.

---
## Requirements & Dependencies
* **Python 3.7+**
* `requests`
* `beautifulsoup4`

---
## Installation
### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/quotes-search-tool.git](https://github.com/your-username/quotes-search-tool.git)
cd quotes-search-tool

```

### 2. Install Dependencies
```bash
pip3 install requests beautifulsoup4

```
---

## Usage
### Mode A: Interactive REPL Mode
Launch the application shell tool and type custom commands straight into the live prompt loop:

```bash
python3 search_tool.py

```
**Console Interface View:**
```text
============================================================
  Quotes Search Tool — [https://quotes.toscrape.com](https://quotes.toscrape.com)
============================================================

search> build
search> find good friends
search> print love
search> quit

```
### Mode B: Single Command CLI Mode
Pass commands and query arguments directly into the standard terminal script handler:

```bash
python3 search_tool.py build
python3 search_tool.py load
python3 search_tool.py print love
python3 search_tool.py find good friends

```

---
## Command Directory
| Command | Description | Example Syntax |
| --- | --- | --- |
| **`build`** | Crawls the website, builds the inverted index, and flushes it to disk. | `build` |
| **`load`** | Loads a previously generated index file directly from disk cache. | `load` |
| **`print <word>`** | Prints every indexed page containing `<word>` along with its frequency. | `print nonsense` |
| **`find <word(s)>`** | Returns all pages containing the given keyword or *all* words inside a phrase. | `find indifference` <br> <br> `find good friends` |
| **`help`** | Displays the diagnostic summary layout of available commands. | `help` |
| **`quit`** | Gracefully breaks execution flow and exits the shell interface. | `quit` |

---
## How It Works
### 1. Crawling Loop
The engine originates at the home page domain and iteratively resolves the `Next` HTML pagination target components until it hits the final leaf node. A mandatory **6 second politeness window constraint** wraps each page request cycle.

### 2. Document Tokenisation & Indexing
Raw text matrices are mined out of every page element specifically targeting quote bodies, author names, and categorical metadata tags. Tokens are transformed into lower case variations and filtered into alphanumeric values. Each unique token points to a tracking array matching the Page URL to its frequency weights.

### 3. Inverted Index JSON Layout
The structured local cache file evaluates state elements matching this JSON structure:

```json
{
  "love": {
    "[https://quotes.toscrape.com/page/1/](https://quotes.toscrape.com/page/1/)": 5,
    "[https://quotes.toscrape.com/page/3/](https://quotes.toscrape.com/page/3/)": 2
  },
  "life": {
    "[https://quotes.toscrape.com/page/1/](https://quotes.toscrape.com/page/1/)": 3
  }
}

```

### 4. Search Execution Strategy
* **Single Word Queries:** Fetches the matching target key and exposes all associated URLs.
* **Multi Word Queries:** Evaluates an intersection lookup pipeline only identifying pages holding **every** specified word from the query array.
* **Evaluation Properties:** Full text search execution behaves completely **case insensitively** (`Love` and `love` match identical keys).
