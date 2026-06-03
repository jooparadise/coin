#!/usr/bin/env python3
"""
DFW Coin Laundry v4 - Google Places verification and discovery

What it does:
1) Verifies named POIs from the v3 CSV using Google Places Text Search (New).
2) Discovers additional laundromat / coin laundry / washateria POIs city-by-city.
3) Deduplicates by Google place id and approximate location.
4) Exports a public-safe CSV/JSON for GitHub Pages.

Set GOOGLE_PLACES_API_KEY in your environment or in a local .env file.
Do not commit the API key to GitHub.
"""
from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"
OUT_DIR.mkdir(exist_ok=True)

INPUT_CSV = DATA_DIR / "DFW_Coin_Laundry_v3_DemandScore_Expanded.csv"
PUBLIC_CSV = DATA_DIR / "DFW_Coin_Laundry_v4_GooglePlaces_Verified.csv"
PUBLIC_JSON = DATA_DIR / "DFW_Coin_Laundry_v4_GooglePlaces_Verified.json"
RAW_JSON = OUT_DIR / f"raw_google_places_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")
BASE_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.businessStatus",
    "places.rating",
    "places.userRatingCount",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.googleMapsUri",
    "places.types",
])

# Coverage targets are intentionally realistic: Dallas/Fort Worth core can exceed 100;
# smaller suburbs usually will not have 100 true coin-laundry storefronts.
CITY_QUERIES = [
    "Dallas", "Fort Worth", "Arlington", "Garland", "Irving", "Grand Prairie",
    "Mesquite", "Carrollton", "Richardson", "Plano", "Lewisville", "Denton",
    "McKinney", "Frisco", "Euless", "Bedford", "Hurst", "Grapevine",
    "Farmers Branch", "DeSoto", "Lancaster", "Cedar Hill", "Duncanville",
    "North Richland Hills", "Watauga", "Keller", "Mansfield", "The Colony",
    "Addison", "Balch Springs", "Coppell", "Allen", "Rowlett", "Sachse",
    "Rockwall", "Seagoville", "Waxahachie", "Burleson", "Weatherford"
]
QUERY_TERMS = ["laundromat", "coin laundry", "washateria", "self service laundry"]

DRY_CLEANER_NEGATIVE_TYPES = {"laundry", "clothing_store"}  # not enough alone; name check below is stricter
POSITIVE_NAME_TERMS = ["laundromat", "laundromats", "coin", "washateria", "laundry", "wash n", "wash &", "lavanderia"]
NEGATIVE_NAME_TERMS = ["dry clean", "cleaners", "alteration", "tailor", "pickup", "delivery only", "commercial laundry"]


def require_api_key() -> None:
    if not API_KEY:
        raise SystemExit(
            "Missing GOOGLE_PLACES_API_KEY. Create a .env file or set the environment variable."
        )


def haversine_mi(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3958.7613
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def places_text_search(query: str, *, lat: Optional[float] = None, lon: Optional[float] = None, radius_m: int = 8000) -> List[Dict[str, Any]]:
    require_api_key()
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body: Dict[str, Any] = {
        "textQuery": query,
        "pageSize": 20,
    }
    if lat is not None and lon is not None:
        body["locationBias"] = {
            "circle": {
                "center": {"latitude": float(lat), "longitude": float(lon)},
                "radius": float(radius_m),
            }
        }
    resp = requests.post(BASE_URL, headers=headers, json=body, timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"Places API error {resp.status_code}: {resp.text[:500]}")
    return resp.json().get("places", [])


def normalize_place(place: Dict[str, Any], source_query: str) -> Dict[str, Any]:
    display = place.get("displayName", {}) or {}
    loc = place.get("location", {}) or {}
    name = display.get("text") or ""
    types = place.get("types") or []
    return {
        "google_place_id": place.get("id"),
        "business_name": name,
        "formatted_address": place.get("formattedAddress"),
        "lat": loc.get("latitude"),
        "lon": loc.get("longitude"),
        "business_status": place.get("businessStatus"),
        "rating": place.get("rating"),
        "review_count": place.get("userRatingCount"),
        "phone": place.get("nationalPhoneNumber"),
        "website": place.get("websiteUri"),
        "google_maps_url": place.get("googleMapsUri"),
        "types": "|".join(types),
        "source_query": source_query,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def classify_coin_laundry(row: Dict[str, Any]) -> Tuple[str, str]:
    name = str(row.get("business_name") or "").lower()
    types = str(row.get("types") or "").lower()
    status = row.get("business_status")

    positive = any(t in name for t in POSITIVE_NAME_TERMS) or "laundry" in types
    negative = any(t in name for t in NEGATIVE_NAME_TERMS)

    if status == "OPERATIONAL" and positive and not negative:
        return "Verified operational candidate", "A"
    if status == "OPERATIONAL" and positive and negative:
        return "Operational but mixed laundry/dry-cleaner; manual review", "B"
    if status in {"CLOSED_TEMPORARILY", "CLOSED_PERMANENTLY"}:
        return f"{status}; exclude from active competition", "D"
    if positive:
        return "Likely laundry; manual review needed", "B"
    return "Low confidence / non-laundromat match", "C"


def verify_existing_named_pois(df: pd.DataFrame, limit: Optional[int] = None) -> pd.DataFrame:
    named = df[df["record_type"].eq("existing_named_poi")].copy()
    if limit:
        named = named.head(limit)
    rows: List[Dict[str, Any]] = []
    for _, r in named.iterrows():
        query_parts = [str(r.get("business_name", "")), str(r.get("address", "")), str(r.get("city", "")), "TX"]
        q = " ".join([x for x in query_parts if x and x != "nan"])
        try:
            places = places_text_search(q, lat=r.get("lat"), lon=r.get("lon"), radius_m=3000)
            for p in places[:3]:
                row = normalize_place(p, q)
                row["matched_from_poi_id"] = r.get("poi_id")
                row["original_business_name"] = r.get("business_name")
                row["original_address"] = r.get("address")
                if row["lat"] and row["lon"] and pd.notna(r.get("lat")) and pd.notna(r.get("lon")):
                    row["distance_from_original_mi"] = round(haversine_mi(float(r["lat"]), float(r["lon"]), float(row["lat"]), float(row["lon"])), 3)
                rows.append(row)
        except Exception as e:
            rows.append({
                "matched_from_poi_id": r.get("poi_id"),
                "original_business_name": r.get("business_name"),
                "original_address": r.get("address"),
                "source_query": q,
                "error": str(e),
                "verified_at_utc": datetime.now(timezone.utc).isoformat(),
            })
        time.sleep(0.15)
    return pd.DataFrame(rows)


def discover_city_places(limit_cities: Optional[int] = None) -> pd.DataFrame:
    cities = CITY_QUERIES[:limit_cities] if limit_cities else CITY_QUERIES
    rows: List[Dict[str, Any]] = []
    for city in cities:
        for term in QUERY_TERMS:
            q = f"{term} in {city}, TX"
            try:
                places = places_text_search(q)
                for p in places:
                    row = normalize_place(p, q)
                    row["discovery_city"] = city
                    row["discovery_term"] = term
                    rows.append(row)
            except Exception as e:
                rows.append({
                    "discovery_city": city,
                    "discovery_term": term,
                    "source_query": q,
                    "error": str(e),
                    "verified_at_utc": datetime.now(timezone.utc).isoformat(),
                })
            time.sleep(0.15)
    return pd.DataFrame(rows)


def dedupe_places(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "google_place_id" in out.columns:
        out = out.sort_values(["google_place_id", "review_count"], ascending=[True, False])
        out = out.drop_duplicates(subset=["google_place_id"], keep="first")
    # Basic lat/lon rounding dedupe for records missing place id.
    if {"lat", "lon"}.issubset(out.columns):
        out["lat_round_4"] = pd.to_numeric(out["lat"], errors="coerce").round(4)
        out["lon_round_4"] = pd.to_numeric(out["lon"], errors="coerce").round(4)
        out = out.sort_values(["lat_round_4", "lon_round_4", "review_count"], ascending=[True, True, False])
        out = out.drop_duplicates(subset=["lat_round_4", "lon_round_4", "business_name"], keep="first")
        out = out.drop(columns=["lat_round_4", "lon_round_4"], errors="ignore")
    return out


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Verify/discover DFW laundromats with Google Places API")
    parser.add_argument("--verify-existing", action="store_true", help="Verify v3 named POIs")
    parser.add_argument("--discover", action="store_true", help="Discover new Google Places city-by-city")
    parser.add_argument("--limit-existing", type=int, default=None, help="Limit named POIs for testing")
    parser.add_argument("--limit-cities", type=int, default=None, help="Limit cities for testing")
    args = parser.parse_args()

    require_api_key()
    v3 = pd.read_csv(INPUT_CSV)
    frames: List[pd.DataFrame] = []
    raw: Dict[str, Any] = {"run_at_utc": datetime.now(timezone.utc).isoformat()}

    if args.verify_existing:
        verified = verify_existing_named_pois(v3, limit=args.limit_existing)
        frames.append(verified)
        raw["verified_existing_count"] = len(verified)

    if args.discover:
        discovered = discover_city_places(limit_cities=args.limit_cities)
        frames.append(discovered)
        raw["discovered_raw_count"] = len(discovered)

    if not frames:
        raise SystemExit("Choose --verify-existing and/or --discover")

    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined = dedupe_places(combined)
    labels = combined.apply(lambda r: classify_coin_laundry(r.to_dict()), axis=1)
    combined["google_verification_status"] = [x[0] for x in labels]
    combined["google_confidence_grade"] = [x[1] for x in labels]

    # Keep a compact public-safe dataset.
    public_cols = [
        "google_place_id", "business_name", "formatted_address", "lat", "lon",
        "business_status", "rating", "review_count", "phone", "website",
        "google_maps_url", "types", "source_query", "discovery_city", "matched_from_poi_id",
        "distance_from_original_mi", "google_verification_status", "google_confidence_grade",
        "verified_at_utc",
    ]
    for col in public_cols:
        if col not in combined.columns:
            combined[col] = None
    combined[public_cols].to_csv(PUBLIC_CSV, index=False)
    combined[public_cols].to_json(PUBLIC_JSON, orient="records", indent=2)

    raw["public_rows"] = len(combined)
    raw["output_csv"] = str(PUBLIC_CSV.relative_to(ROOT))
    raw["output_json"] = str(PUBLIC_JSON.relative_to(ROOT))
    RAW_JSON.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    print(f"Wrote {PUBLIC_CSV}")
    print(f"Wrote {PUBLIC_JSON}")


if __name__ == "__main__":
    main()
