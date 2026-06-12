# 재무관리 (Google Sheets + Docs)

투자 중심 **2인 가구** 재무관리 시스템입니다. Google Sheets에서 일별 지출·수입·보유 종목을 관리하고, **한눈에보기** 탭에서 KPI와 차트를 확인합니다.

📖 **자세한 설명서:** [`docs/사용설명서.md`](docs/사용설명서.md) — 시트별 설명, 입력법, FAQ, **처음 배포 0→1** 전체 과정

---

## 처음 배포하기 (요약)

> **아직 한 번도 올리지 않았다면** 아래만 따라 하세요. 상세 스크린샷·FAQ는 [사용설명서](docs/사용설명서.md)를 참고하세요.

### 1. Google Cloud (최초 1회, ~10분)

1. [Google Cloud Console](https://console.cloud.google.com) → 새 프로젝트
2. [API 라이브러리](https://console.cloud.google.com/apis/library)에서 **4개 사용**  
   Sheets · Docs · Drive · **Apps Script**
3. **OAuth 동의 화면** → 외부 → **테스트 사용자**에 본인 Gmail 추가
4. **사용자 인증 정보** → OAuth 클라이언트 ID → **데스크톱 앱** → JSON 다운로드
5. JSON을 `config/credentials.json`으로 저장

### 2. PC에서 배포 실행

```powershell
cd "c:\Users\Temp\Desktop\현철\코딩연습\재무관리 프로그램"
pip install -r requirements.txt
python setup.py deploy
```

- 브라우저에서 Google **로그인·권한 허용**
- 완료 시 **Spreadsheet URL** 출력 → **즐겨찾기 저장**

### 3. 배포 직후 (Spreadsheet에서)

1. **`설정`** — Person1/Person2 이름, 목표 순자산, **월 예산 한도**
2. **F5 새로고침** → **재무관리 → ⚙ 트리거 설치**
3. **`자산_종목`** — 보유 계좌·종목 (C열 **담당자** = 설정 이름)
4. **재무관리 → 📊 갱신 → 시세+환율+일별자산**

이후 매일은 **Spreadsheet URL**만 열면 됩니다. 로컬 폴더는 재배포·수정할 때만 필요합니다.

---

## 주요 기능

- **한눈에보기** — 유일한 허브: KPI 5개 + 차트 2개 + 탭 바로가기
- **2인 자산** — `자산_종목` C열 담당자, `계좌목록` 자동 집계
- **일별 자산 추이** — Person1 / Person2 / 합계 (09:00 자동)
- **예산 vs 실적** — 설정 월 한도 ↔ 지출 자동 비교
- **비상자금** — (현금+CMA) ÷ 월지출 = N개월
- **해외 투자** — US(USD), CN(위안), Yahoo 시세·환율
- **세금한도 · DSR · 만기 · 시나리오 · 자산 이동**
- **월말** — 순자산 스냅샷 + Google Docs 리포트

---

## 탭 구조 (19개)

| 자주 씀 | 시트 |
|--------|------|
| ★★★ | **한눈에보기**, 자산_종목, 지출, 수입 |
| ★★ | 부채, 자산_일별이력, 세금한도, DSR, 설정 |
| 가끔 | 자산_이동, 시나리오, 만기, 계좌목록 |
| 상세 | **대시보드** (마지막 탭 — 상세 KPI) |

전체 설명: [사용설명서 — 시트별 설명](docs/사용설명서.md#시트별-설명-19개-탭)

---

## 시세·환율 (중요)

**HTS 실시간이 아닙니다.** Yahoo Finance → **15~20분 지연** 가능.

| 갱신 | 메뉴 **시세+환율+일별자산** 또는 매일 **09:00** (트리거) |
| 원화 평가 | `자산_종목` **I열** 자동 (F×H×환율) |

---

## 파일 구조

```
재무관리 프로그램/
├── README.md                 ← 이 파일 (빠른 시작)
├── docs/
│   └── 사용설명서.md         ← 📖 자세한 설명서
├── setup.py                  ← python setup.py deploy
├── requirements.txt
├── config/
│   ├── credentials.json      ← 직접 넣음 (Git 금지)
│   └── token.json            ← deploy 후 자동 생성
├── deploy/                   ← 시트 생성 Python
├── apps-script/              ← 메뉴·시세·자동화
└── sheets/template-spec.md   ← 개발자용 시트 명세
```

---

## 문제 해결

| 증상 | 해결 |
|------|------|
| 메뉴 없음 | F5 새로고침, Apps Script에서 `onOpen` 실행 |
| access blocked | OAuth **테스트 사용자**에 Gmail 추가 |
| 403 API | API **4개** 활성화 확인 |
| credentials 없음 | `config/credentials.json` 경로 확인 |

→ 더 많은 FAQ: [사용설명서 — 문제 해결](docs/사용설명서.md#문제-해결-faq)

---

## 재배포 주의

`python setup.py deploy`를 **다시 실행하면 새 Spreadsheet**가 만들어집니다.  
기존 데이터는 유지되지 않으니 Drive에서 백업 후 진행하세요.

---

## 보안

`config/credentials.json`, `config/token.json` — **절대 공유·업로드 금지**
