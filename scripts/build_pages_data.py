#!/usr/bin/env python3
"""Build a static map data file. If Google-verified data exists, prefer it; otherwise use v3 data."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
verified_csv = DATA / "DFW_Coin_Laundry_v4_GooglePlaces_Verified.csv"
v3_csv = DATA / "DFW_Coin_Laundry_v3_DemandScore_Expanded.csv"
out_json = DATA / "map_data_current.json"

if verified_csv.exists():
    df = pd.read_csv(verified_csv)
    df["record_type"] = "google_places_verified"
    df["map_color"] = df.get("google_confidence_grade", "C").map({"A":"green","B":"yellow","C":"red","D":"gray"}).fillna("gray")
    df["name"] = df["business_name"]
    df["address"] = df["formatted_address"]
else:
    df = pd.read_csv(v3_csv)
    df["name"] = df["business_name"]

df.to_json(out_json, orient="records", indent=2)
print(f"Wrote {out_json}")
