# GitHub 업로드 및 온라인 지도 배포 절차

## 1) 새 Repository 만들기

GitHub에서 새 repository를 만듭니다. 예:

`dfw-coin-laundry-map`

## 2) 파일 업로드

이 패키지의 모든 파일을 repository에 업로드합니다.

터미널을 쓰는 경우:

```bash
git init
git add .
git commit -m "Initial DFW coin laundry map"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/dfw-coin-laundry-map.git
git push -u origin main
```

## 3) Google Places API Key 저장

GitHub repository에서:

`Settings → Secrets and variables → Actions → New repository secret`

이름:

`GOOGLE_PLACES_API_KEY`

값:

Google Cloud Console에서 만든 Places API key

주의: API key를 `index.html`이나 public JS 파일에 직접 넣지 마세요.

## 4) GitHub Pages 활성화

`Settings → Pages`에서 Source를 **GitHub Actions**로 선택합니다.

## 5) 검증 실행

`Actions → Verify Google Places and Publish Pages → Run workflow`

실행 후 `data/DFW_Coin_Laundry_v4_GooglePlaces_Verified.csv`와 JSON이 업데이트되고, 온라인 지도가 GitHub Pages로 배포됩니다.

## 6) 데이터 해석 기준

- `google_confidence_grade = A`: 운영 중으로 보이는 강한 후보
- `B`: 운영 중이지만 dry cleaner/wash & fold 혼합 가능성, 수동 확인 필요
- `C`: 낮은 신뢰도, 지도 표시 가능하지만 경쟁 계산에는 주의
- `D`: 폐업/임시폐업 가능성, active competition에서 제외 권장

## 7) 다음 개선

Google Places 검증 후에는 다음 데이터를 추가하면 투자용 정확도가 올라갑니다.

- ACS tract/block group 실제 spatial join
- Apartment complex / multifamily parcel layer
- Traffic count / parking / visibility
- Lease vacancy / rent estimate
- Review count velocity
- Competitor machine count / operating hours / wash & fold 여부
