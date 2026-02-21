"""
Sri Lanka Property Scraper
==========================
Sources:
  ikman.lk  - land-for-sale, houses, apartments-for-sale (26 ads/page)
  lankapropertyweb.com - article.listing-item with from_index pagination (30/page)
Target : 5000+ raw non-preprocessed records
Output : dataset/properties_raw.csv
Run    : python -u dataset/scrape_properties.py
"""

import requests
import json
import re
import time
import csv
import random
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

OUTPUT_CSV = Path(__file__).parent / "properties_raw.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

FIELDNAMES = [
    "source", "title", "price_lkr", "price_raw",
    "location", "district", "property_type", "ad_type",
    "bedrooms", "bathrooms", "land_size_perches", "floor_area_sqft",
    "description", "url", "scraped_at",
]

# ikman.lk categories (slug, ad_type, max_pages)
IKMAN_CATEGORIES = [
    ("land-for-sale",       "for_sale", 200),  # 31k listings
    ("houses",              "for_sale",  80),  # 19k listings
    ("apartments-for-sale", "for_sale",  80),  # 3k listings
]

def log(msg):
    print(msg, flush=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def extract_ikman_json(html: str) -> dict:
    marker = "window.initialData = {"
    idx = html.find(marker)
    if idx == -1:
        return {}
    start = idx + len(marker) - 1
    text = html[start:]
    depth, end = 0, 0
    for i, ch in enumerate(text):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    try:
        return json.loads(text[:end])
    except json.JSONDecodeError:
        return {}


def parse_price(raw: str):
    if not raw:
        return None
    raw = str(raw).strip()
    # "Rs. 72M"
    m = re.search(r"([\d,\.]+)\s*[Mm]\b", raw)
    if m:
        try:
            return float(m.group(1).replace(",", "")) * 1_000_000
        except ValueError:
            pass
    # "Rs 53,000,000"
    m = re.search(r"Rs\.?\s*([\d,]+)", raw)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def safe_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def safe_float(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


# ── ikman.lk scraper ──────────────────────────────────────────────────────────

def scrape_ikman_category(session, slug: str, ad_type: str, max_pages: int) -> list:
    records = []
    consecutive_empty = 0

    for page in range(1, max_pages + 1):
        url = f"https://ikman.lk/en/ads/sri-lanka/{slug}?page={page}"
        try:
            resp = session.get(url, timeout=25)

            if resp.status_code == 403:
                log(f"    [{slug}] Page {page}: 403 blocked")
                break
            if resp.status_code != 200:
                log(f"    [{slug}] Page {page}: HTTP {resp.status_code} - skipping")
                time.sleep(3)
                continue

            data = extract_ikman_json(resp.text)
            ads  = (data.get("serp", {})
                        .get("ads", {})
                        .get("data", {})
                        .get("ads", []))

            if not ads:
                consecutive_empty += 1
                log(f"    [{slug}] Page {page}: empty ({consecutive_empty}/3)")
                if consecutive_empty >= 3:
                    log(f"    [{slug}] 3 consecutive empty pages - stopping")
                    break
                time.sleep(2)
                continue

            consecutive_empty = 0  # reset on success

            for ad in ads:
                price_raw = str(ad.get("price", "") or "")
                price_lkr = parse_price(price_raw)
                details   = str(ad.get("details", "") or "")

                bedrooms = None
                m = re.search(r"Bedrooms?[:\s]+(\d+)", details, re.I)
                if m:
                    bedrooms = safe_int(m.group(1))

                bathrooms = None
                m = re.search(r"Bathrooms?[:\s]+(\d+)", details, re.I)
                if m:
                    bathrooms = safe_int(m.group(1))

                land_size = None
                m = re.search(r"([\d\.]+)\s*perch", details, re.I)
                if m:
                    land_size = safe_float(m.group(1))

                floor_area = None
                m = re.search(r"([\d,]+)\s*sq\.?\s*ft", details, re.I)
                if m:
                    floor_area = safe_float(m.group(1))

                location  = str(ad.get("location", "") or "")
                cat       = ad.get("category", {})
                prop_type = cat.get("name", "") if isinstance(cat, dict) else str(cat)
                slug_val  = str(ad.get("slug", "") or "")

                records.append({
                    "source":            "ikman.lk",
                    "title":             str(ad.get("title", "") or ""),
                    "price_lkr":         price_lkr,
                    "price_raw":         price_raw,
                    "location":          location,
                    "district":          location,
                    "property_type":     prop_type,
                    "ad_type":           ad_type,
                    "bedrooms":          bedrooms,
                    "bathrooms":         bathrooms,
                    "land_size_perches": land_size,
                    "floor_area_sqft":   floor_area,
                    "description":       details,
                    "url":               f"https://ikman.lk/en/ad/{slug_val}",
                    "scraped_at":        datetime.now().isoformat(),
                })

            log(f"    [{slug}] Page {page:>3}: +{len(ads):>2}  cat total={len(records):>4}")
            time.sleep(random.uniform(1.0, 2.5))

        except requests.Timeout:
            log(f"    [{slug}] Page {page}: timeout")
            time.sleep(10)
        except requests.RequestException as e:
            log(f"    [{slug}] Page {page}: {e}")
            time.sleep(5)

    return records


def scrape_all_ikman() -> list:
    session = requests.Session()
    session.headers.update(HEADERS)
    all_records = []
    seen_urls   = set()

    for slug, ad_type, max_pages in IKMAN_CATEGORIES:
        log(f"\n  Category: {slug}  (max {max_pages} pages)")
        cat_recs = scrape_ikman_category(session, slug, ad_type, max_pages)
        new_recs = [r for r in cat_recs if r["url"] not in seen_urls]
        for r in new_recs:
            seen_urls.add(r["url"])
        log(f"  => {len(new_recs)} new unique from {slug} (running total: {len(all_records)+len(new_recs)})")
        all_records.extend(new_recs)

    return all_records


# ── lankapropertyweb.com scraper ───────────────────────────────────────────────

def get_lpw_cards(soup):
    """Walk up from property_details links to find listing-item articles."""
    seen, cards = set(), []
    for a in soup.find_all("a", href=re.compile("property_details")):
        node = a.parent
        for _ in range(12):
            if node is None:
                break
            if "listing-item" in (node.get("class") or []):
                if id(node) not in seen:
                    seen.add(id(node))
                    cards.append(node)
                break
            node = node.parent
    return cards


def parse_lpw_card(card) -> dict | None:
    text = card.get_text(" ", strip=True)

    link_a = card.find("a", href=re.compile("property_details"))
    title  = ""
    if link_a:
        h = link_a.find(["h2", "h3", "h4"])
        title = (h.get_text(strip=True) if h else link_a.get_text(strip=True))[:200]
    if not title:
        h = card.find(["h2", "h3", "h4"])
        title = h.get_text(strip=True)[:200] if h else ""
    if not title:
        return None

    # Price
    price_raw = ""
    for s in card.find_all(string=re.compile(r"Rs\.?\s*[\d,]")):
        pt = s.parent.get_text(strip=True) if s.parent else ""
        if re.search(r"Rs\.?\s*[\d,]", pt):
            price_raw = pt[:100]
            break
    price_lkr = parse_price(price_raw)

    # Location from title or body
    location = ""
    m = re.search(
        r"\b(Colombo\s*\d*|Negombo|Kandy|Galle|Matara|Kurunegala|Ratnapura|"
        r"Kalutara|Gampaha|Kotte|Nugegoda|Battaramulla|Malabe|Kaduwela|"
        r"Homagama|Pannipitiya|Maharagama|Dehiwala|Moratuwa|Piliyandala|"
        r"Wattala|Ja-Ela|Kelaniya|Kiribathgoda|Kadawatha)\b",
        text, re.I,
    )
    if m:
        location = m.group(1)

    bedrooms = None
    m = re.search(r"(\d+)\s*(?:bed|BR|bedroom)", text, re.I)
    if m:
        bedrooms = safe_int(m.group(1))

    bathrooms = None
    m = re.search(r"(\d+)\s*(?:bath|bathroom)", text, re.I)
    if m:
        bathrooms = safe_int(m.group(1))

    land_size = None
    m = re.search(r"([\d\.]+)\s*perch", text, re.I)
    if m:
        land_size = safe_float(m.group(1))

    floor_area = None
    m = re.search(r"([\d,]+)\s*sq\.?\s*ft", text, re.I)
    if m:
        floor_area = safe_float(m.group(1))

    prop_type = ""
    m = re.search(
        r"\b(house|villa|apartment|flat|land|commercial|annex|duplex|bungalow|penthouse)\b",
        text, re.I,
    )
    if m:
        prop_type = m.group(1).title()

    href = link_a["href"] if link_a else ""
    if href and not href.startswith("http"):
        href = "https://www.lankapropertyweb.com" + href

    return {
        "source":            "lankapropertyweb.com",
        "title":             title,
        "price_lkr":         price_lkr,
        "price_raw":         price_raw,
        "location":          location,
        "district":          "",
        "property_type":     prop_type,
        "ad_type":           "for_sale",
        "bedrooms":          bedrooms,
        "bathrooms":         bathrooms,
        "land_size_perches": land_size,
        "floor_area_sqft":   floor_area,
        "description":       text[:300],
        "url":               href,
        "scraped_at":        datetime.now().isoformat(),
    }


def scrape_lpw(needed: int = 2000) -> list:
    records = []
    session = requests.Session()
    session.headers.update(HEADERS)
    from_index      = 0
    step            = 30
    consecutive_empty = 0

    while len(records) < needed:
        url = (
            "https://www.lankapropertyweb.com/sale/"
            if from_index == 0
            else (
                f"https://www.lankapropertyweb.com/sale/index.php"
                f"?search=1&from_index={from_index}&price-option=price_total"
            )
        )
        try:
            resp = session.get(url, timeout=25)
            if resp.status_code != 200:
                log(f"  [lpw] from_index={from_index}: HTTP {resp.status_code} - stopping")
                break

            soup  = BeautifulSoup(resp.text, "lxml")
            cards = get_lpw_cards(soup)

            if not cards:
                consecutive_empty += 1
                log(f"  [lpw] from_index={from_index}: no cards ({consecutive_empty}/3)")
                if consecutive_empty >= 3:
                    break
                from_index += step
                time.sleep(2)
                continue

            consecutive_empty = 0
            page_count = 0
            for card in cards:
                rec = parse_lpw_card(card)
                if rec:
                    records.append(rec)
                    page_count += 1

            log(f"  [lpw] from_index={from_index:>5}: +{page_count:>2}  total={len(records):>5}")
            from_index += step
            time.sleep(random.uniform(1.5, 3.0))

        except requests.Timeout:
            log(f"  [lpw] from_index={from_index}: timeout")
            time.sleep(10)
        except requests.RequestException as e:
            log(f"  [lpw] from_index={from_index}: {e}")
            time.sleep(5)

    return records


# ── Save CSV ───────────────────────────────────────────────────────────────────

def save_csv(records: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)
    log(f"Saved {len(records):,} records -> {path.name}")


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log("=" * 60)
    log("  Sri Lanka Property Scraper")
    log(f"  Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"  Target  : 5000+ records -> {OUTPUT_CSV.name}")
    log("=" * 60)

    all_records = []

    # ── Phase 1: ikman.lk ─────────────────────────────────────────────────────
    log("\n[Phase 1] Scraping ikman.lk (3 categories) ...")
    ikman_recs = scrape_all_ikman()
    all_records.extend(ikman_recs)
    log(f"\nikman.lk TOTAL: {len(ikman_recs):,} unique records")

    save_csv(all_records, OUTPUT_CSV)

    # ── Phase 2: lankapropertyweb.com ─────────────────────────────────────────
    needed = max(0, 5000 - len(all_records))
    if needed > 0:
        log(f"\n[Phase 2] Scraping lankapropertyweb.com (need {needed} more) ...")
        lpw_recs = scrape_lpw(needed=needed + 500)
        all_records.extend(lpw_recs)
        log(f"\nlankapropertyweb.com TOTAL: {len(lpw_recs):,} records")
    else:
        log("\n[Phase 2] Skipped - already >= 5000 records.")

    save_csv(all_records, OUTPUT_CSV)

    log("\n" + "=" * 60)
    log(f"  DONE - {len(all_records):,} raw records saved.")
    log(f"  File : {str(OUTPUT_CSV)}")
    log("=" * 60)
