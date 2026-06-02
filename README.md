# DFW Coin Laundry Site Screening v4

This repository publishes an online DFW coin laundry map and includes a Google Places API verification workflow.

## What is included

- `index.html` — static DFW map for GitHub Pages
- `data/DFW_Coin_Laundry_v3_DemandScore_Expanded.csv` — v3 demand score model
- `scripts/google_places_verify.py` — verifies/discovers laundromat POIs using Google Places API Text Search (New)
- `.github/workflows/verify-places-and-pages.yml` — optional GitHub Actions workflow to run verification and publish GitHub Pages

## Important data note

The v3 dataset includes both named public listings and density seed rows. Density seed rows are not confirmed real businesses. The Google Places verification workflow is designed to replace/augment those seeds with verified Google Place records.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and add GOOGLE_PLACES_API_KEY
python scripts/google_places_verify.py --verify-existing --discover
python scripts/build_pages_data.py
```

For a test run:

```bash
python scripts/google_places_verify.py --verify-existing --discover --limit-existing 5 --limit-cities 2
```

## GitHub Pages setup

1. Create a new GitHub repository.
2. Upload/push this folder to the repository.
3. In GitHub, go to **Settings → Secrets and variables → Actions**.
4. Add repository secret: `GOOGLE_PLACES_API_KEY`.
5. Go to **Settings → Pages** and choose **GitHub Actions** as the build/deploy source.
6. Go to **Actions → Verify Google Places and Publish Pages → Run workflow**.

The public website will be available through the GitHub Pages URL after deployment.

## Recommended API restrictions

In Google Cloud Console, restrict the key to Places API only. If you run verification only from GitHub Actions, do not put the key inside `index.html`.


## v5.1 업데이트: Location Checker

`index.html` 왼쪽 패널에 주소 입력 분석 기능이 추가되었습니다. 주소를 입력하면 해당 지점의 3-mile 경쟁 수, nearest competitor, 주변 demand proxy, demand_score, opportunity_score, 투자 판단 문구를 표시합니다.

기본 주소 변환은 OpenStreetMap Nominatim을 사용합니다. Google Places API key는 여전히 GitHub Actions Secret에서만 사용하며 public HTML에는 넣지 않습니다.


## v5.1 변경사항
- Location Check 기본 경쟁 반경을 2 miles로 변경했습니다.
- 반경 옵션: 1 / 2 / 3 / 5 miles 선택 가능.
- 분석 결과의 경쟁 카운트 라벨을 `Existing POI {radius}mi`로 명확히 변경했습니다.
