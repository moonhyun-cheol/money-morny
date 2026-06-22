"""현철·여친 가구 인생 플랜 상수 (2026-06 기준)."""

from __future__ import annotations

# ── 인물 ──
PERSON1_NAME = "현철"
PERSON2_NAME = "여친"
MARRIAGE_PLAN = "2027년 말 ~ 2028년 (비혼 기간 세금·저축 최적화)"
HOUSING_GOAL = "파주 운정 59형 신축 입주 (목표 2031~2032)"

# ── 연소득 (세전, 만원) ──
ANNUAL_INCOME_P1 = 3300  # 본인
ANNUAL_INCOME_P2 = 2590  # 여친 (주40h·최저·주휴 포함)
ANNUAL_INCOME_HOUSEHOLD = ANNUAL_INCOME_P1 + ANNUAL_INCOME_P2

# ── 월 세후 수입 (원) ──
NET_INCOME_P1 = 2_500_000
NET_INCOME_P2 = 1_900_000
NET_INCOME_HOUSEHOLD = NET_INCOME_P1 + NET_INCOME_P2  # 4_400_000

# ── 월 고정비 (원) ──
FIXED_RENT = 700_000
FIXED_ELECTRIC = 40_000
FIXED_PHONE = 60_000
FIXED_TRANSPORT = 100_000
FIXED_INSURANCE = 250_000
FIXED_SUBSCRIPTION = 150_000
FIXED_LOAN_GENERAL = 92_000  # 300만, 연 6.6%, 36개월
# 햇살론+장학금 300만 → 별도 최소 상환, 고정비 제외

FIXED_MONTHLY_TOTAL = (
    FIXED_RENT
    + FIXED_ELECTRIC
    + FIXED_PHONE
    + FIXED_TRANSPORT
    + FIXED_INSURANCE
    + FIXED_SUBSCRIPTION
    + FIXED_LOAN_GENERAL
)  # 1_392_000

# ── 식비·용돈 (원/월) ──
FOOD_GROCERY = 750_000  # 주 1회 장보기 15~20만
ALLOWANCE_P1 = 150_000
ALLOWANCE_P2 = 100_000

# ── 투자·저축 (원/월, 8월~ 가구 합산) ──
SAVE_YOUTH_LEAP = 700_000  # 청년도약 (본인만)
SAVE_ISA = 500_000
SAVE_HOUSE = 550_000
SAVE_PENSION_P1 = 200_000  # 연 240만 → 세액공제 (여유 시 400만까지 상향)
SAVE_PENSION_P2 = 0  # 외국인·저소득 → 환급 효과 미미
SAVE_VISA_BUFFER_P2 = 50_000  # TOPIK6, 목표 300만
SAVE_SUBSCRIPTION_MIN = 0  # 청약 640만 유지·추가납입은 여유 시

MONTHLY_INVEST_TOTAL = (
    SAVE_YOUTH_LEAP
    + SAVE_ISA
    + SAVE_HOUSE
    + SAVE_PENSION_P1
    + SAVE_VISA_BUFFER_P2
    + SAVE_SUBSCRIPTION_MIN
)  # 2_000_000 — 세후 440만과 합산 일치

# ── 교통 (K-패스 전 지출, 참고) ──
TRANSIT_P1_DAILY = 9_700
TRANSIT_P2_DAILY = 3_800
TRANSIT_P1_DAYS = 22
TRANSIT_P2_DAYS = 17  # 주 4일

# ── 목표 ──
GOAL_NET_WORTH = 150_000_000  # 입주 전 순자산 목표 (원)
GOAL_DATE = "2032-06-30"
CONTRACT_DEPOSIT_TARGET = 50_000_000
MOVE_IN_CASH_TARGET = 100_000_000

# ── 세금 (비혼, 연간) ──
PENSION_LIMIT_P1 = 6_000_000
PENSION_TAX_CREDIT_RATE = 0.15  # 총급여 5,500만 이하
PENSION_PLAN_P1 = 2_400_000  # 연 납입 (월 20만, 상향 여지)
ISA_ANNUAL_LIMIT = 20_000_000
YOUTH_LEAP_MONTHLY_MAX = 700_000

# ── 투자 종목 템플릿 (자산_종목 시드) ──
INVESTMENT_PRODUCTS = [
    {
        "account_type": "적금",
        "account_name": "현철-청년도약",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": "청년도약계좌",
        "qty": 1,
        "price": 0,
        "note": "월 70만, 5년 만기·주택 특별해지",
    },
    {
        "account_type": "ISA",
        "account_name": "현철-ISA서민형",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": "MMF/예금",
        "qty": 1,
        "price": 0,
        "note": "월 55만, 2029 계약금, 예금·MMF만",
    },
    {
        "account_type": "주택청약",
        "account_name": "현철-청약통장",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": "주택청약종합저축",
        "qty": 1,
        "price": 6_400_000,
        "note": "11년 가입, 640만 유지",
    },
    {
        "account_type": "연금저축",
        "account_name": "현철-연금저축",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": "연금저축",
        "qty": 1,
        "price": 0,
        "note": "연 300~400만, 세액공제 15%",
    },
    {
        "account_type": "현금",
        "account_name": "집마련-공동",
        "owner": "공동",
        "ticker": "",
        "name": "집마련 통장",
        "qty": 1,
        "price": 0,
        "note": "월 65만, 잔금·부대비",
    },
    {
        "account_type": "현금",
        "account_name": "여친-비자비상",
        "owner": PERSON2_NAME,
        "ticker": "",
        "name": "비자·비상",
        "qty": 1,
        "price": 0,
        "note": "TOPIK6, 목표 300만",
    },
]

LIABILITIES = [
    {
        "type": "신용대출",
        "name": "일반대출",
        "principal": 3_000_000,
        "balance": 3_000_000,
        "rate": 6.6,
        "monthly": 92_000,
        "maturity": "2029-06-01",
        "memo": "고정비 반영",
    },
    {
        "type": "기타",
        "name": "햇살론+장학금",
        "principal": 3_000_000,
        "balance": 3_000_000,
        "rate": 3.0,
        "monthly": 0,
        "maturity": "",
        "memo": "최소 상환, 고정비 제외",
    },
]

# 월 예산 (Google Sheets 설정 시트용, 원)
MONTHLY_BUDGET: dict[str, int] = {
    "식비": FOOD_GROCERY,
    "교통": FIXED_TRANSPORT,
    "쇼핑": ALLOWANCE_P1 + ALLOWANCE_P2,
    "고정비": FIXED_RENT + FIXED_ELECTRIC + FIXED_PHONE + FIXED_INSURANCE + FIXED_SUBSCRIPTION,
    "의료": 0,
    "여가": 0,
    "대출상환": FIXED_LOAN_GENERAL,
    "대출이자": 0,
    "기타": SAVE_VISA_BUFFER_P2,
}

LIABILITY_SAMPLE = LIABILITIES
