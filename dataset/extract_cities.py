"""
extract_cities.py
=================
Enriches existing properties_raw.csv with city-level locations
extracted from listing titles and descriptions.

ikman.lk stores district-level location in the JSON 'location' field.
But listing TITLES contain the city: e.g. "3BR House in Nugegoda for Sale"
This script extracts those city names and updates the location column.

Run: python dataset/extract_cities.py
"""

import pandas as pd
import re
from pathlib import Path

RAW_CSV = Path(__file__).parent / "properties_raw.csv"

# ── City → District mapping (Sri Lanka) ──────────────────────────────────────
CITY_TO_DISTRICT = {
    # Colombo District suburbs/cities
    "Dehiwala":          "Colombo", "Mount Lavinia":     "Colombo",
    "Moratuwa":          "Colombo", "Nugegoda":          "Colombo",
    "Maharagama":        "Colombo", "Battaramulla":      "Colombo",
    "Kaduwela":          "Colombo", "Malabe":            "Colombo",
    "Pannipitiya":       "Colombo", "Homagama":          "Colombo",
    "Piliyandala":       "Colombo", "Kottawa":           "Colombo",
    "Boralesgamuwa":     "Colombo", "Angoda":            "Colombo",
    "Kolonnawa":         "Colombo", "Rajagiriya":        "Colombo",
    "Talawatugoda":      "Colombo", "Kotte":             "Colombo",
    "Athurugiriya":      "Colombo", "Padukka":           "Colombo",
    "Avissawella":       "Colombo", "Hanwella":          "Colombo",
    "Thalawathugoda":    "Colombo", "Wellampitiya":      "Colombo",
    "Nawala":            "Colombo", "Narahenpita":       "Colombo",
    "Dematagoda":        "Colombo", "Maradana":          "Colombo",
    "Kotahena":          "Colombo", "Grandpass":         "Colombo",
    "Bambalapitiya":     "Colombo", "Havelock Town":     "Colombo",
    "Thurstan":          "Colombo", "Borella":           "Colombo",
    "Cinnamon Gardens":  "Colombo", "Colombo 1":         "Colombo",
    "Colombo 2":         "Colombo", "Colombo 3":         "Colombo",
    "Colombo 4":         "Colombo", "Colombo 5":         "Colombo",
    "Colombo 6":         "Colombo", "Colombo 7":         "Colombo",
    "Colombo 8":         "Colombo", "Colombo 9":         "Colombo",
    "Colombo 10":        "Colombo", "Colombo 11":        "Colombo",
    "Colombo 12":        "Colombo", "Colombo 13":        "Colombo",
    "Colombo 14":        "Colombo", "Colombo 15":        "Colombo",
    "Colombo":           "Colombo",

    # Gampaha District
    "Negombo":           "Gampaha", "Wattala":           "Gampaha",
    "Ja-Ela":            "Gampaha", "Kelaniya":          "Gampaha",
    "Kiribathgoda":      "Gampaha", "Kadawatha":         "Gampaha",
    "Ragama":            "Gampaha", "Gampaha":           "Gampaha",
    "Minuwangoda":       "Gampaha", "Ekala":             "Gampaha",
    "Veyangoda":         "Gampaha", "Nittambuwa":        "Gampaha",
    "Mirigama":          "Gampaha", "Divulapitiya":      "Gampaha",
    "Ganemulla":         "Gampaha", "Katunayake":        "Gampaha",
    "Seeduwa":           "Gampaha", "Peliyagoda":        "Gampaha",
    "Hendala":           "Gampaha", "Dalugama":          "Gampaha",

    # Kalutara District
    "Kalutara":          "Kalutara", "Panadura":         "Kalutara",
    "Horana":            "Kalutara", "Bandaragama":      "Kalutara",
    "Ingiriya":          "Kalutara", "Agalawatta":       "Kalutara",
    "Aluthgama":         "Kalutara", "Beruwala":         "Kalutara",
    "Wadduwa":           "Kalutara", "Payagala":         "Kalutara",
    "Matugama":          "Kalutara", "Bulathsinhala":    "Kalutara",

    # Kandy District
    "Kandy":             "Kandy",   "Peradeniya":       "Kandy",
    "Katugastota":       "Kandy",   "Gampola":          "Kandy",
    "Nawalapitiya":      "Kandy",   "Akurana":          "Kandy",
    "Digana":            "Kandy",   "Kundasale":        "Kandy",
    "Ampitiya":          "Kandy",   "Gelioya":          "Kandy",

    # Galle District
    "Galle":             "Galle",   "Hikkaduwa":        "Galle",
    "Ambalangoda":       "Galle",   "Elpitiya":         "Galle",
    "Karandeniya":       "Galle",   "Baddegama":        "Galle",
    "Bentota":           "Galle",   "Balapitiya":       "Galle",

    # Matara District
    "Matara":            "Matara",  "Weligama":         "Matara",
    "Mirissa":           "Matara",  "Dickwella":        "Matara",
    "Akuressa":          "Matara",  "Deniyaya":         "Matara",
    "Kamburupitiya":     "Matara",  "Hakmana":          "Matara",

    # Hambantota District
    "Hambantota":        "Hambantota", "Tangalle":      "Hambantota",
    "Tissamaharama":     "Hambantota", "Ambalantota":   "Hambantota",
    "Suriyawewa":        "Hambantota",

    # Kurunegala District
    "Kurunegala":        "Kurunegala", "Kuliyapitiya":  "Kurunegala",
    "Narammala":         "Kurunegala", "Pannala":       "Kurunegala",
    "Giriulla":          "Kurunegala", "Alawwa":        "Kurunegala",

    # Puttalam District
    "Puttalam":          "Puttalam",  "Chilaw":         "Puttalam",
    "Wennappuwa":        "Puttalam",  "Marawila":       "Puttalam",

    # Anuradhapura District
    "Anuradhapura":      "Anuradhapura", "Mihintale":   "Anuradhapura",
    "Kekirawa":          "Anuradhapura",

    # Others — district = major city
    "Polonnaruwa":       "Polonnaruwa",
    "Badulla":           "Badulla",     "Bandarawela":   "Badulla",
    "Ella":              "Badulla",     "Haputale":      "Badulla",
    "Monaragala":        "Monaragala",
    "Ratnapura":         "Ratnapura",   "Embilipitiya":  "Ratnapura",
    "Kegalle":           "Kegalle",     "Mawanella":     "Kegalle",
    "Nuwara Eliya":      "Nuwara Eliya","Hatton":        "Nuwara Eliya",
    "Jaffna":            "Jaffna",      "Chavakachcheri":"Jaffna",
    "Vavuniya":          "Vavuniya",
    "Trincomalee":       "Trincomalee",
    "Batticaloa":        "Batticaloa",
    "Ampara":            "Ampara",      "Kalmunai":      "Ampara",
    "Matale":            "Matale",
}

DISTRICTS = set(CITY_TO_DISTRICT.values())

# Build a sorted list of cities by length (longest first) to avoid partial matches
CITIES_SORTED = sorted(CITY_TO_DISTRICT.keys(), key=len, reverse=True)

def extract_city_from_text(text: str) -> str | None:
    """Search listing title/description for a known city name."""
    if not isinstance(text, str):
        return None
    # Try each city with word boundary matching
    for city in CITIES_SORTED:
        pattern = r'\b' + re.escape(city) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            return city
    return None


def main():
    print(f"Loading: {RAW_CSV}")
    df = pd.read_csv(RAW_CSV)
    print(f"Loaded {len(df):,} rows")
    print(f"Current location unique values: {df['location'].nunique()} → {sorted(df['location'].dropna().unique())[:8]}...")

    # Extract city from title first, then description as fallback
    print("\nExtracting city names from titles and descriptions...")

    title_city = df["title"].apply(extract_city_from_text)
    desc_city  = df.get("description", pd.Series([None]*len(df))).apply(extract_city_from_text)

    city_series = title_city.combine_first(desc_city)

    # Stats
    found = city_series.notna().sum()
    print(f"City found in title:        {title_city.notna().sum():,} / {len(df):,} ({title_city.notna().mean()*100:.1f}%)")
    print(f"City found in desc fallback: {(desc_city.notna() & title_city.isna()).sum():,}")
    print(f"Total city extraction rate:  {found:,} / {len(df):,} ({found/len(df)*100:.1f}%)")

    # For rows where we found a city, update location to the city
    # For rows without city, keep existing district-level location
    df["city"] = city_series.fillna(df["location"])  # fallback to district

    # Update location: use city name if found (more specific), else keep district
    df["location"] = city_series.combine_first(df["location"]).str.strip()

    # Update district to always be the district (inferred from city)
    df["district"] = df["city"].map(CITY_TO_DISTRICT).fillna(df["district"])

    # Summary of new locations
    print(f"\nNew location unique values: {df['location'].nunique()}")
    print("\nTop 20 locations after enrichment:")
    print(df["location"].value_counts().head(20).to_string())

    print(f"\nCity count distribution (cities with >= 20 listings):")
    vc = df["location"].value_counts()
    print(vc[vc >= 20].to_string())

    # Save back
    df.to_csv(RAW_CSV, index=False)
    print(f"\n✅ Saved enriched data → {RAW_CSV}")
    print(f"   Locations upgraded from district to city: {found:,} rows")


if __name__ == "__main__":
    main()
