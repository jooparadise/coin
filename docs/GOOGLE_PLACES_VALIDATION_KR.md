# Google Places API 검증 로직

## 목적

v3 데이터의 한계는 일부 row가 실제 Google Maps 운영 매장으로 검증되지 않았다는 점입니다. v4 검증은 다음을 목표로 합니다.

1. 기존 named POI가 Google Places에 존재하는지 확인
2. `businessStatus`로 운영 중/폐업/임시폐업 구분
3. `place_id`, 정확 좌표, 리뷰 수, 평점, 전화번호, 웹사이트, Google Maps URL 확보
4. DFW 도시별 추가 laundromat/coin laundry/washateria 검색
5. 중복 제거 후 지도 데이터로 변환

## 검색어

- `laundromat in {city}, TX`
- `coin laundry in {city}, TX`
- `washateria in {city}, TX`
- `self service laundry in {city}, TX`

## 필드

현재 스크립트는 다음 필드를 요청합니다.

- Google place id
- business name
- formatted address
- lat/lon
- business status
- rating / review count
- phone / website
- Google Maps URL
- place types

## 분류 기준

| Grade | 의미 |
|---|---|
| A | `OPERATIONAL` + laundromat/coin/washateria 계열 이름/타입 |
| B | 운영 중이지만 dry cleaner 혼합 가능성 또는 수동검토 필요 |
| C | 낮은 신뢰도 또는 비코인런드리 가능성 |
| D | 폐업/임시폐업 가능성 |

## 주의

Google Places API는 유료 API이며 요청 필드/호출 수에 따라 과금될 수 있습니다. 테스트는 `--limit-existing`, `--limit-cities` 옵션으로 시작하세요.
