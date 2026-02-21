"""
Sri Lanka Property Scraper  (v2 — with listed_at)
==========================
Sources:
  ikman.lk  - land-for-sale, houses, apartments-for-sale (26 ads/page)
  lankapropertyweb.com - article.listing-item with from_index pagination (30/page)

NEW in v2:
  - Extracts `listed_at` from ikman.lk JSON (the date the seller posted the ad)
  - Extracts `posted_days_ago` for reference
  - This gives us a real 90-day time series of property prices!

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
from datetime import datetime, timedelta

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

# ── UPDATED FIELDNAMES: added listed_at and posted_days_ago ───────────────────
FIELDNAMES = [
    "source", "title", "price_lkr", "price_raw",
    "location", "district", "property_type", "ad_type",
    "bedrooms", "bathrooms", "land_size_perches", "floor_area_sqft",
    "description", "url",
    "listed_at",        # ← NEW: date the ad was originally posted on ikman.lk
    "posted_days_ago",  # ← NEW: how many days ago it was posted (integer)
    "scraped_at",
]

# ikman.lk categories (slug, ad_type, max_pages)
IKMAN_CATEGORIES = [
    ("land-for-sale",       "for_sale", 200),  # ~31k listings
    ("houses",              "for_sale",  80),  # ~19k listings
    ("apartments-for-sale", "for_sale",  80),  # ~3k listings
]

def log(msg):
    # Safe print for Windows terminals that don't support full Unicode (e.g. cp1252)
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        safe_msg = msg.encode("ascii", errors="replace").decode("ascii")
        print(safe_msg, flush=True)


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


def parse_relative_time(time_str: str) -> tuple[str, int] | tuple[None, None]:
    """
    Parse ikman.lk relative time strings into (iso_date, days_ago).

    ikman.lk uses these formats in `timeStamp` and `lastBumpUpDate`:
      - "just now", "a minute ago"
      - "4 minutes", "15 hours"
      - "3 days", "2 weeks"
      - "1 month", "3 months"
      - "bump_up"  ← means re-bumped, ignore for original posting estimate
    """
    if not time_str or time_str.strip().lower() in ("bump_up", "", "just now", "a minute ago"):
        days_ago = 0
        dt = datetime.now() - timedelta(days=days_ago)
        return dt.isoformat(), days_ago

    s = time_str.strip().lower()

    m = re.search(r"(\d+)\s*minute", s)
    if m:
        dt = datetime.now() - timedelta(minutes=int(m.group(1)))
        return dt.isoformat(), 0

    m = re.search(r"(\d+)\s*hour", s)
    if m:
        dt = datetime.now() - timedelta(hours=int(m.group(1)))
        return dt.isoformat(), 0

    m = re.search(r"(\d+)\s*day", s)
    if m:
        days = int(m.group(1))
        dt = datetime.now() - timedelta(days=days)
        return dt.isoformat(), days

    m = re.search(r"(\d+)\s*week", s)
    if m:
        days = int(m.group(1)) * 7
        dt = datetime.now() - timedelta(days=days)
        return dt.isoformat(), days

    m = re.search(r"(\d+)\s*month", s)
    if m:
        days = int(m.group(1)) * 30
        dt = datetime.now() - timedelta(days=days)
        return dt.isoformat(), days

    return None, None


def parse_ikman_date(ad: dict) -> tuple[str, int | None]:
    """
    Extract the posting date from ikman.lk ad JSON.

    Real fields found in ikman.lk JSON:
      - timeStamp     : original posting time (relative string)
      - lastBumpUpDate: when seller last bumped (relative string)

    We use timeStamp as the original listed date.
    If timeStamp is 'bump_up', the ad was re-bumped — we use lastBumpUpDate
    as a lower bound (the bump happened at most X ago,  so original post
    could be older; we estimate it as +7 days older).

    Returns: (listed_at_iso_str, posted_days_ago_int)
    """
    timestamp_str  = str(ad.get("timeStamp",     "") or "")
    bump_date_str  = str(ad.get("lastBumpUpDate", "") or "")

    if timestamp_str and timestamp_str.lower() != "bump_up":
        # timeStamp is the original posting time
        listed_at, days_ago = parse_relative_time(timestamp_str)
        return listed_at, days_ago
    elif bump_date_str:
        # Ad was bumped — bump date is MORE RECENT than original post
        # Add 7 days offset as an estimate (bumped ads are typically 1-4 weeks old)
        listed_at, days_ago = parse_relative_time(bump_date_str)
        if days_ago is not None:
            days_ago_est = days_ago + 7  # estimate original post was ~7 days before bump
            dt = datetime.now() - timedelta(days=days_ago_est)
            return dt.isoformat(), days_ago_est
        return listed_at, days_ago

    return None, None


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
    date_found_count = 0   # track how many ads have a date

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

                # ── NEW: extract listed_at date ────────────────────────────────
                listed_at, posted_days_ago = parse_ikman_date(ad)

                # Debug: on first page, log ALL keys available in first ad
                if page == 1 and len(records) == 0:
                    log(f"    [{slug}] First ad keys: {list(ad.keys())}")
                    log(f"    [{slug}] listed_at={listed_at}, days_ago={posted_days_ago}")

                if listed_at:
                    date_found_count += 1

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
                    "listed_at":         listed_at,         # ← NEW
                    "posted_days_ago":   posted_days_ago,   # ← NEW
                    "scraped_at":        datetime.now().isoformat(),
                })

            log(f"    [{slug}] Page {page:>3}: +{len(ads):>2}  total={len(records):>4}  dated={date_found_count}")
            time.sleep(random.uniform(1.0, 2.5))

        except requests.Timeout:
            log(f"    [{slug}] Page {page}: timeout")
            time.sleep(10)
        except requests.RequestException as e:
            log(f"    [{slug}] Page {page}: {e}")
            time.sleep(5)

    log(f"    [{slug}] DONE: {len(records)} records, {date_found_count} with listing date ({date_found_count*100//max(len(records),1)}%)")
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
        "listed_at":         None,   # lankapropertyweb doesn't expose posting date
        "posted_days_ago":   None,
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
    log("  Sri Lanka Property Scraper  v2 (with listing dates)")
    log(f"  Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"  Target  : 5000+ records -> {OUTPUT_CSV.name}")
    log("=" * 60)

    all_records = []

    # ── Phase 1: ikman.lk ─────────────────────────────────────────────────────
    log("\n[Phase 1] Scraping ikman.lk (3 categories) ...")
    ikman_recs = scrape_all_ikman()
    all_records.extend(ikman_recs)
    log(f"\nikman.lk TOTAL: {len(ikman_recs):,} unique records")

    # Quick date stats
    dated = [r for r in ikman_recs if r.get("listed_at")]
    log(f"  Ads with listing date: {len(dated):,} ({len(dated)*100//max(len(ikman_recs),1)}%)")
    if dated:
        dates = sorted([r["listed_at"] for r in dated])
        log(f"  Date range: {dates[0][:10]} → {dates[-1][:10]}")

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
