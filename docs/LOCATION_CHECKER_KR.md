# v5.1 Location Checker 사용법

이 버전은 지도 왼쪽 패널에 `Location Check` 기능을 추가합니다.

## 기능

1. 주소 입력
2. 주소를 좌표로 변환
3. 선택한 반경, 기본 2 miles, 안의 경쟁 POI 계산
4. 주변 기존 POI를 바탕으로 소득, renter %, multifamily %, 차량 미보유율, 인구밀도 proxy 추정
5. demand_score와 opportunity_score 산출
6. 투자 판단 문구 표시
7. Google Maps 바로가기 제공

## API key 보안 구조

브라우저에서 주소를 입력하는 기능은 기본적으로 OpenStreetMap Nominatim geocoding을 사용합니다. Google Places API key는 public HTML에 넣지 않습니다.

Google Places API key는 GitHub Actions Secret에만 저장하고, 운영 중 매장 검증 workflow에서만 사용합니다.

## 점수 해석

- Green: 수요와 경쟁 여백이 양호한 후보
- Yellow: 조건부 검토 후보
- Red: 보수적으로 접근해야 하는 후보

## 주의

이 기능은 투자 결정을 자동으로 내려주는 것이 아니라, 1차 스크리닝 도구입니다. 최종 판단 전에는 임대료, CAM, 유틸리티, 주차, zoning, equipment cost, 주변 아파트 세탁시설 보급률, 실제 Google Places 검증 결과를 확인해야 합니다.


## v5.1 변경사항
- Location Check 기본 경쟁 반경을 2 miles로 변경했습니다.
- 반경 옵션: 1 / 2 / 3 / 5 miles 선택 가능.
- 분석 결과의 경쟁 카운트 라벨을 `Existing POI {radius}mi`로 명확히 변경했습니다.
