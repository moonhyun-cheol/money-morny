"""현철·여친 가구 인생 플랜 상수 (2026-06 기준, KB 거래내역 반영)."""

from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, timedelta

# ── 인물 ──
PERSON1_NAME = "현철"
PERSON2_NAME = "여친"
MARRIAGE_PLAN = "2027년 말 ~ 2028년 (비혼 기간 세금·저축 최적화)"
HOUSING_GOAL = "파주 운정 59형 신축 입주 (목표 2031~2032)"

# ── 연소득 (세전, 만원) — P2는 아래 산출 후 갱신 ──
ANNUAL_INCOME_P1 = 3300  # 계약연봉 (수습 90% 기간 별도)

# ── 현철 급여 (계약연봉 3,300만 · 2026-05-18 입사 · 수습 3개월) ──
P1_START_DATE = date(2026, 5, 18)
P1_CONTRACT_ANNUAL = 33_000_000
P1_GROSS_MONTHLY = P1_CONTRACT_ANNUAL // 12  # 2,750,000
P1_PROBATION_MONTHS = 3
P1_PROBATION_RATE = 0.90  # 취업규칙 90% 가정 — 실제 지급률 확인 후 수정
P1_PROBATION_END = date(2026, 8, 17)  # 입사+3개월-1일
P1_PAYDAY_NOTE = "익월 급여 (전월 근무분)"
P1_GROSS_PROBATION = int(P1_GROSS_MONTHLY * P1_PROBATION_RATE)  # 2,475,000


def _estimate_monthly_net(gross: int) -> int:
    """월 세전 → 세후 (4대보험·소득세 간이). 부양가족·비과세 수당 없음 가정."""
    pension = int(gross * 0.045)
    hi = int(gross * 0.03545 * 1.1295)
    ei = int(gross * 0.009)
    taxable = gross - pension - hi - ei
    income_tax = int(taxable * 0.033 * 1.1)
    return gross - pension - hi - ei - income_tax


# 세전 3,300만÷12=275만 → 세후 (수습은 세전 90% 후 동일 공제)
NET_INCOME_P1 = _estimate_monthly_net(P1_GROSS_MONTHLY)
NET_INCOME_P1_PROBATION = _estimate_monthly_net(P1_GROSS_PROBATION)

# ── 여친 아르바이트 (2026 최저임금 · 4대보험 · 주5 월화수토일) ──
# 근로 10:00~22:00 · 무급 휴게 2h → 유급 10h/일 · 주40h 초과 연장 1.5배 · 주휴수당
P2_MIN_WAGE_HOURLY = 10_320  # 2026년 최저시급
P2_SHIFT_START = 10  # 10:00
P2_SHIFT_END = 22  # 22:00
P2_BREAK_HOURS = 2
P2_PAID_HOURS_DAILY = P2_SHIFT_END - P2_SHIFT_START - P2_BREAK_HOURS  # 10
P2_WORK_WEEKDAYS = (0, 1, 2, 5, 6)  # 월·화·수·토·일
P2_WEEKLY_SCHEDULED_DAYS = len(P2_WORK_WEEKDAYS)  # 5
P2_OVERTIME_MULTIPLIER = 1.5
P2_WORK_START_DATE = date(2026, 7, 1)  # 7/1 출근 → 8월 첫 급여(7월분)
P2_WORK_START = "2026-07"
P2_WORK_SCHEDULE = "월화수토일"  # 목·금 휴무
P2_FIRST_PAYCHECK_YEAR = 2026
P2_FIRST_PAYCHECK_MONTH = 8  # 소득 입금은 8월부터 (익월 지급)
P2_FIRST_PAYCHECK = f"{P2_FIRST_PAYCHECK_YEAR}-{P2_FIRST_PAYCHECK_MONTH:02d}"
P2_PAYDAY_NOTE = "익월 급여 (전월 근무분)"


def _p2_scheduled_days_in_iso_week(iso_year: int, iso_week: int) -> int:
    jan4 = date(iso_year, 1, 4)
    week1_mon = jan4 - timedelta(days=jan4.weekday())
    monday = week1_mon + timedelta(days=(iso_week - 1) * 7)
    return sum(
        1 for i in range(7) if (monday + timedelta(days=i)).weekday() in P2_WORK_WEEKDAYS
    )


def _p2_week_gross(worked_days: int, scheduled_days: int) -> int:
    hours = worked_days * P2_PAID_HOURS_DAILY
    regular = min(hours, 40) * P2_MIN_WAGE_HOURLY
    overtime = int(max(hours - 40, 0) * P2_MIN_WAGE_HOURLY * P2_OVERTIME_MULTIPLIER)
    weekly_holiday = (
        P2_PAID_HOURS_DAILY * P2_MIN_WAGE_HOURLY
        if worked_days >= scheduled_days and scheduled_days > 0 and hours >= 15
        else 0
    )
    return regular + overtime + weekly_holiday


def p2_gross_for_work_month(year: int, month: int) -> int:
    """해당 월 근무분 세전 (최저임금·주휴·연장·개근 반영)."""
    days_in = calendar.monthrange(year, month)[1]
    work_days = [
        date(year, month, day)
        for day in range(1, days_in + 1)
        if date(year, month, day).weekday() in P2_WORK_WEEKDAYS
        and date(year, month, day) >= P2_WORK_START_DATE
    ]
    if not work_days:
        return 0
    weeks: dict[tuple[int, int], int] = defaultdict(int)
    for worked_on in work_days:
        weeks[worked_on.isocalendar()[:2]] += 1
    return sum(
        _p2_week_gross(worked, _p2_scheduled_days_in_iso_week(iso[0], iso[1]))
        for iso, worked in weeks.items()
    )


def p2_net_for_work_month(year: int, month: int) -> int:
    return _estimate_monthly_net(p2_gross_for_work_month(year, month))


# 대표 월(10월) — 건보·연간 소득·정상 가구 합산 기준
GROSS_INCOME_P2_MONTHLY = p2_gross_for_work_month(2026, 10)
NET_INCOME_P2 = p2_net_for_work_month(2026, 9)  # 10월 입금(9월 근무) · 플랜 기준
ANNUAL_INCOME_P2 = sum(p2_gross_for_work_month(2026, m) for m in range(1, 13)) // 10_000
ANNUAL_INCOME_HOUSEHOLD = ANNUAL_INCOME_P1 + ANNUAL_INCOME_P2
NET_INCOME_HOUSEHOLD = NET_INCOME_P1 + NET_INCOME_P2  # 10월~ 정상 가구 세후

# ── [1] 주거·공과 (개인 고정비 · 평소 반반, 결제만 공동통장) ──
FIXED_RENT = 600_000  # 월세+관리비
FIXED_ELECTRIC = 50_000
FIXED_SHARED = FIXED_RENT + FIXED_ELECTRIC  # 650,000
FIXED_SHARED_HALF = FIXED_SHARED // 2  # 325,000 — 8월~ 인당
# 7월만: 여친 소득 0 → 현철이 월세·전기 전액 (평소 ½씩)

# ── [2] 통신 ──
FIXED_PHONE_KT = 2_890
FIXED_PHONE_SKT = 160_000  # 요금+휴대폰 교체할부 포함
FIXED_PHONE_P2 = 20_000  # 여친
FIXED_PHONE = FIXED_PHONE_KT + FIXED_PHONE_SKT + FIXED_PHONE_P2

# ── [3] 보험 (KB 2026-06-04 첫 납부 138,290) ──
FIXED_INSURANCE = 138_290

# ── [4] 구독 (원/월) ──
SUB_ICLOUD = 5_000  # 실청구 ~4,400 · 카카오페이 5,000 가정
SUB_COUPANG = 7_890
SUB_LIMBUS = 100_000  # 림버스 구독 상향 (구 14,800)
SUB_SPOTIFY = 11_990
SUB_YOUTUBE = 10_900  # 구 14,900(토스·21일) → 2026-05~ 갈아탐
SUB_CURSOR_KRW = 120_000  # Cursor Pro+ 구독 (2026-06~ · 월 12만)
SUB_PIKPAK = 4_581  # Pickpack · CMA 정기 · 2026-08~
FIXED_SUBSCRIPTION = (
    SUB_ICLOUD + SUB_COUPANG + SUB_LIMBUS + SUB_SPOTIFY + SUB_YOUTUBE + SUB_CURSOR_KRW
)  # 78,580
FIXED_SUBSCRIPTION_AUGUST = FIXED_SUBSCRIPTION + SUB_PIKPAK  # 83,161

# ── [5] 대출 ──
LOAN_SCHOLAR_PRINCIPAL = 3_000_000
LOAN_SCHOLAR_RATE = 0.03
FIXED_LOAN_SCHOLAR_INTEREST = int(LOAN_SCHOLAR_PRINCIPAL * LOAN_SCHOLAR_RATE / 12)  # 7,500

LOAN_KAKAO_PRINCIPAL = 3_000_000
LOAN_KAKAO_RATE = 0.067
LOAN_KAKAO_MONTHS = 36
FIXED_LOAN_KAKAO = 92_220  # KB 미출금 · 카뱅 등 확인

# ── [6] 여친 건강보험 (직장가입·8월~ · 위 GROSS_INCOME_P2_MONTHLY) ──
NHIS_EMPLOYEE_RATE = 0.03545
NHIS_LONGTERM_RATE = 0.1295
FIXED_NHIS_P2 = int(GROSS_INCOME_P2_MONTHLY * NHIS_EMPLOYEE_RATE * (1 + NHIS_LONGTERM_RATE))  # 86,488

# ── [7] 교통 — 정가 (요금×출근일, K-패스 미반영) ──
TRANSIT_P1_FARE = 9_800
TRANSIT_P1_DAYS = 22  # 월~금 · 주 5일
TRANSIT_P2_FARE = 3_500
TRANSIT_P2_DAYS = 22  # 월화수토일 · 주 5일 (52주÷12≈22일)
TRANSIT_P1_GROSS = TRANSIT_P1_FARE * TRANSIT_P1_DAYS
TRANSIT_P2_GROSS = TRANSIT_P2_FARE * TRANSIT_P2_DAYS
TRANSIT_GROSS = TRANSIT_P1_GROSS + TRANSIT_P2_GROSS

FIXED_TRANSPORT_P1 = TRANSIT_P1_GROSS
FIXED_TRANSPORT_P2 = TRANSIT_P2_GROSS
FIXED_TRANSPORT = TRANSIT_GROSS

FIXED_LOAN_GENERAL = FIXED_LOAN_SCHOLAR_INTEREST + FIXED_LOAN_KAKAO

FIXED_MONTHLY_TOTAL = (
    FIXED_RENT
    + FIXED_ELECTRIC
    + FIXED_PHONE
    + FIXED_INSURANCE
    + FIXED_SUBSCRIPTION
    + FIXED_LOAN_SCHOLAR_INTEREST
    + FIXED_LOAN_KAKAO
    + FIXED_NHIS_P2
    + FIXED_TRANSPORT
)  # 1,335,270

# ── 인당 고정비 (월세·전기 ½ + 전용) — 8월~ ──
FIXED_P1_EXCLUSIVE = (
    FIXED_PHONE_KT
    + FIXED_PHONE_SKT
    + FIXED_INSURANCE
    + FIXED_SUBSCRIPTION
    + FIXED_LOAN_SCHOLAR_INTEREST
    + FIXED_LOAN_KAKAO
    + FIXED_TRANSPORT_P1
)  # 519,492 — 월세·전기 제외
FIXED_P2_EXCLUSIVE = FIXED_PHONE_P2 + FIXED_NHIS_P2 + FIXED_TRANSPORT_P2  # 165,778 (8월~)
FIXED_P1_TOTAL = FIXED_P1_EXCLUSIVE + FIXED_SHARED_HALF  # 844,492
FIXED_P2_TOTAL = FIXED_P2_EXCLUSIVE + FIXED_SHARED_HALF  # 490,778

# 7월: 여친 소득 없음 · 월세·전기 전액 + P2 전화·교통 (건보는 8월 급여부터)
FIXED_JULY_TOTAL = FIXED_MONTHLY_TOTAL - FIXED_NHIS_P2
# 7월 현철 개인고정 = 월세전기 전액 + 본인전용 + 여친 통신·교통
FIXED_P1_JULY = (
    FIXED_SHARED
    + FIXED_P1_EXCLUSIVE
    + FIXED_PHONE_P2
    + FIXED_TRANSPORT_P2
)  # == FIXED_JULY_TOTAL
FIXED_P1_ONLY_TOTAL = FIXED_MONTHLY_TOTAL - FIXED_P2_EXCLUSIVE  # 6월 등 P2 근무 전

# 고정비 항목 — (항목명, 월금액, 담당, 메모)
# 월세·관리·전기: 개인고정 ½ · 결제 KB공동 / 7월 현철 전액(+여친 통신·교통)
FIXED_COST_ITEMS: list[tuple[str, int, str, str]] = [
    ("월세+관리비", FIXED_RENT, PERSON1_NAME, "개인고정·평소 ½ · 7월 전액 →KB공동"),
    ("전기", FIXED_ELECTRIC, PERSON1_NAME, "개인고정·평소 ½ · 7월 전액 →KB공동"),
    ("KT", FIXED_PHONE_KT, PERSON1_NAME, "FBS ~23일"),
    ("SKT", FIXED_PHONE_SKT, PERSON1_NAME, "요금+휴대폰 교체할부"),
    ("통신(여친)", FIXED_PHONE_P2, PERSON2_NAME, "8월~ 여친 우리통장"),
    ("보험", FIXED_INSURANCE, PERSON1_NAME, "2026-06-04 KB카드"),
    ("iCloud", SUB_ICLOUD, PERSON1_NAME, "카카오 ~5천"),
    ("쿠팡 와우", SUB_COUPANG, PERSON1_NAME, "27일"),
    ("림버스컴퍼니", SUB_LIMBUS, PERSON1_NAME, "구독 10만"),
    ("Spotify", SUB_SPOTIFY, PERSON1_NAME, "3일"),
    ("YouTube Premium", SUB_YOUTUBE, PERSON1_NAME, "28일 전후"),
    ("Cursor", SUB_CURSOR_KRW, PERSON1_NAME, "Pro+ 12만/월"),
    ("Pickpack", SUB_PIKPAK, PERSON1_NAME, "CMA정기 · 8월~"),
    ("장학금 이자", FIXED_LOAN_SCHOLAR_INTEREST, PERSON1_NAME, "27일 ~2,887"),
    ("카카오 긴급생활", FIXED_LOAN_KAKAO, PERSON1_NAME, "KB 0회·카뱅 확인"),
    ("건강보험(여친)", FIXED_NHIS_P2, PERSON2_NAME, "8월 첫 급여~ 직장가입"),
    ("교통(현철)", FIXED_TRANSPORT_P1, PERSON1_NAME, "정가 왕복 9800×22"),
    ("교통(여친)", FIXED_TRANSPORT_P2, PERSON2_NAME, f"8월~ 여친 · {P2_WORK_SCHEDULE}"),
]

# ── 식비·용돈 ──
FOOD_GROCERY = 550_000
ALLOWANCE_P1 = 100_000  # 토스 용돈 (구 150,000 → 차액 집마련)
ALLOWANCE_P2 = 300_000  # 카카오페이 용돈 (구 200,000 → 차액 토스저축)
SAVE_MIN_RATE = 0.5  # 개인 세후 소득의 최소 50% 저축

# 7월 축소 (현철 월급만)
FOOD_JULY = 550_000
ALLOWANCE_P1_JULY = 100_000
ALLOWANCE_P2_JULY = 0


def food_split_for_save_targets(
    p1_net: int,
    p2_net: int,
    food_total: int = FOOD_GROCERY,
    *,
    fixed_p1: int | None = None,
    fixed_p2: int | None = None,
    allow_p1: int | None = None,
    allow_p2: int | None = None,
) -> tuple[int, int]:
    """공동 식비 — 두 사람 저축률(세후 대비) 최솟값이 최대가 되도록 분배."""
    fp1 = FIXED_P1_TOTAL if fixed_p1 is None else fixed_p1
    fp2 = FIXED_P2_TOTAL if fixed_p2 is None else fixed_p2
    ap1 = ALLOWANCE_P1 if allow_p1 is None else allow_p1
    ap2 = ALLOWANCE_P2 if allow_p2 is None else allow_p2
    if p2_net <= 0:
        return food_total, 0
    best_p1_food = 0
    best_score = -1.0
    # P1 식비 몫을 조정해 두 사람 저축률의 최솟값을 최대화 (목표 각 50%)
    for p1_food in range(0, food_total + 1, 1_000):
        p2_food = food_total - p1_food
        s1 = personal_savings(p1_net, fp1, p1_food, ap1)
        s2 = personal_savings(p2_net, fp2, p2_food, ap2)
        score = min(s1 / p1_net, s2 / p2_net)
        if score > best_score:
            best_score = score
            best_p1_food = p1_food
    return best_p1_food, food_total - best_p1_food


def personal_savings(net: int, fixed: int, food: int, allowance: int) -> int:
    return max(net - fixed - food - allowance, 0)

# ── 투자·저축 (10월~ 정상, 세후 가구 ~470만 기준) ──
# 집마련: 2029 ISA 만기까지 ISA에 최대 적립 → 만기 시 계약금·중도금
# CMA=비상금만(15~30만) · 2029 이후 잔금·입주자금=파킹 · 연금=입주 후
ISA_MONTHLY_CAP = 20_000_000 // 12  # 서민형 ISA 연 한도
SAVE_YOUTH_LEAP = 0
SAVE_YOUTH_FUTURE_TARGET_YEAR = 2027
SAVE_YOUTH_FUTURE_MONTHLY = 500_000
ISA_MATURITY_APPROX = "2029-06"  # 기존 3년 ISA · 잔여 ~2년11개월(2026-07)
SAVE_CMA_EMERGENCY = 200_000  # 비상금만 · 15~30만
SAVE_PENSION_P1 = 0
SAVE_PENSION_P1_AFTER_MOVE_IN = 200_000
SAVE_VISA_BUFFER_P2 = 50_000  # P2 토스 저축 내 비자 목표(집저축과 동일 통장)
SAVE_SUBSCRIPTION_MIN = 0

# 식비 분배 고정 (재조정 시 주초유 몫 유지 · 자동 재분배 방지)
FOOD_P1, FOOD_P2 = 74_000, 476_000
SAVE_P1_TOTAL = personal_savings(
    NET_INCOME_P1, FIXED_P1_TOTAL, FOOD_P1, ALLOWANCE_P1
)
SAVE_P2_TOTAL = personal_savings(
    NET_INCOME_P2, FIXED_P2_TOTAL, FOOD_P2, ALLOWANCE_P2
)
SAVE_ISA = min(
    max(SAVE_P1_TOTAL - SAVE_CMA_EMERGENCY, 0),
    ISA_MONTHLY_CAP,
)  # 집마련 · 만기 ~2029
SAVE_P2_TOSS_MONTHLY = SAVE_P2_TOTAL  # 비자+집마련 합산(토스 1통장)

_remainder = (
    NET_INCOME_HOUSEHOLD - FIXED_MONTHLY_TOTAL - FOOD_GROCERY - ALLOWANCE_P1 - ALLOWANCE_P2
)
SAVE_HOUSE = SAVE_ISA + SAVE_CMA_EMERGENCY + SAVE_P2_TOSS_MONTHLY

MONTHLY_INVEST_TOTAL = SAVE_P1_TOTAL + SAVE_P2_TOTAL

SAVE_HOUSE_P1 = max(SAVE_P1_TOTAL - SAVE_CMA_EMERGENCY, 0)  # ISA 집마련분
SAVE_HOUSE_P2 = SAVE_P2_TOSS_MONTHLY

# ── 실제 통장 (2026-07 정리) ──
# 용돈 통장(토스 현철·카카오페이 주초유)은 **개설·등록**하되 7월 이체 금액은 0(펀딩 보류)
# 1 KB 문현철 고정비 · 2 KB 공동 월세·관리비 · 3 하나 청약 · 4 카카오페이 식비
# 5 토스 용돈(금액0) · 6 삼성증권 저축 · 7 우리 주초유 고정비 · 8 토스 주초유 저축 · 9 카카오페이 주초유 용돈(금액0)
P1_SALARY_HUB = "KB 문현철"
P1_SALARY_ACCT = "938002005252755"
HOUSEHOLD_JOINT_BANK = "KB 공동통장"
HOUSEHOLD_JOINT_ACCT = "59220101780144"
P1_SUBSCRIPTION_BANK = "하나 청약"
P1_CHEONGYAK_ACCT = "44891006625125"
CHEONGYAK_BALANCE = 6_400_000
CHEONGYAK_MONTHLY = 20_000
P1_FOOD_WALLET = "카카오페이(현철)"  # 식비 공동 · 카드 미수령
P1_ALLOWANCE_BANK = "토스(현철)"
P1_ALLOWANCE_ACCT = "1000-35463755"
P1_SECURITIES = "삼성증권"  # 개인저축 (8월~ CMA·ISA·연금 가능)
P1_SECURITIES_JULY = "삼성증권 자유입출금"  # 7월은 펀드 말고 자유입출금에 예치
P2_SALARY_BANK = "우리(주초유)"
P2_SALARY_ACCT = "1002662688244"
P2_SAVE_BANK = "토스(주초유)"  # 저축
P2_ALLOWANCE_BANK = "카카오페이(주초유)"  # 용돈 통장(개설) · 금액은 보류
P2_TOSS_BANK = P2_SAVE_BANK  # legacy alias

COHAB_JOINT_ID = "가계공동"
COHAB_HUB_ID = COHAB_JOINT_ID
COHAB_HUB_INSTITUTION = HOUSEHOLD_JOINT_BANK
P1_PERSONAL_HUB_ID = "P1-고정비"
P2_TOSS_ACCOUNT_ID = "P2-토스저축"

# 물리 9: 위 목록 전부 (용돈 통장 포함 · 이체액만 0)
PHYSICAL_ACCOUNT_COUNT = 9
PHYSICAL_ACCOUNT_COUNT_JULY = 7  # 현철 5 + 용돈통장2(잔액0) · 여친 우리/토스저축은 8월~
ALLOWANCE_FUNDING_PAUSED = True  # 통장은 있음 · 7월 용돈 이체액 0
JULY_TO_ALLOWANCE_P1 = 50_000  # KB→토스 용돈 (7/7)
JULY_ALLOWANCE_SHOES = 19_000
JULY_ALLOWANCE_SNACK = 16_061  # 간식 · 7/8
JULY_ALLOWANCE_BALANCE = JULY_TO_ALLOWANCE_P1 - JULY_ALLOWANCE_SHOES - JULY_ALLOWANCE_SNACK  # 14,939
JULY_TO_ALLOWANCE_P2 = 0
ACCOUNTS_TO_OPEN: list[dict[str, str]] = []  # 실계좌 기준 추가 개설 없음

# 이체: 공동=월세·관리·전기 / 식비=카카오페이
# 7월: 주거 전액+여친 통신·교통도 현철 (건보는 8월~)
COHAB_P1_TRANSFER = FIXED_SHARED_HALF  # 8월~ 월세·관리·전기 ½
COHAB_P1_TRANSFER_JULY = FIXED_SHARED  # 7월 월세·관리·전기 전액 (65만)
COHAB_CONTRIBUTION_P2 = FIXED_SHARED_HALF
FOOD_P1_TO_KAKAOPAY = FOOD_P1
FOOD_P2_TO_KAKAOPAY = FOOD_P2
FOOD_JULY_TO_KAKAOPAY = FOOD_JULY
HOUSEHOLD_JOINT_OUTFLOW = FIXED_SHARED  # 공동 = 월세+관리+전기
HOUSEHOLD_JOINT_BUFFER = FIXED_SHARED
HOUSEHOLD_JOINT_BUFFER_JULY = FIXED_SHARED
HOUSEHOLD_HUB_BUFFER = HOUSEHOLD_JOINT_BUFFER
PARKING_P1 = FIXED_P1_EXCLUSIVE  # KB 남김 = 본인 전용만 (주거는 공동)
PARKING_P2 = FIXED_P2_EXCLUSIVE

# 7월 여친 고정비(건보 제외) — 현철이 부담하되 **우리(주초유) 고정비 통장으로 이체**
FIXED_P2_JULY_ON_P1 = FIXED_PHONE_P2 + FIXED_TRANSPORT_P2  # 97,000
JULY_TO_P2_FIXED = FIXED_P2_JULY_ON_P1  # KB문현철 → 우리(주초유)
# KB 남김(이체 전) = 본인전용 + 여친분 / 이체·카뱅 후 = 본인전용 − 카뱅
FIXED_P1_JULY_ON_KB = FIXED_P1_EXCLUSIVE + FIXED_P2_JULY_ON_P1  # 758,080 (이체 전)
FIXED_P1_JULY_ON_KB_AFTER = FIXED_P1_EXCLUSIVE - FIXED_LOAN_KAKAO  # 568,860 (여친분이체+카뱅납부 후)
JULY_TO_JOINT = COHAB_P1_TRANSFER_JULY  # 650,000
JULY_TO_FOOD = FOOD_JULY_TO_KAKAOPAY  # 550,000
JULY_TO_CHEONGYAK = CHEONGYAK_MONTHLY  # 20,000

HOUSEHOLD_JOINT_ITEMS: list[tuple[str, int, str]] = [
    ("월세+관리비", FIXED_RENT, HOUSEHOLD_JOINT_BANK),
    ("전기", FIXED_ELECTRIC, HOUSEHOLD_JOINT_BANK),
]

FIXED_P1_ITEMS: list[tuple[str, int, str]] = [
    ("월세·관리·전기 ½→KB공동", COHAB_P1_TRANSFER, HOUSEHOLD_JOINT_BANK),
    ("식비 몫→카카오페이", FOOD_P1, P1_FOOD_WALLET),
    ("KT", FIXED_PHONE_KT, P1_SALARY_HUB),
    ("SKT", FIXED_PHONE_SKT, P1_SALARY_HUB),
    ("보험", FIXED_INSURANCE, P1_SALARY_HUB),
    ("구독 합", FIXED_SUBSCRIPTION, P1_SALARY_HUB),
    ("장학금 이자", FIXED_LOAN_SCHOLAR_INTEREST, P1_SALARY_HUB),
    ("카카오 긴급", FIXED_LOAN_KAKAO, P1_SALARY_HUB),
    ("교통", FIXED_TRANSPORT_P1, P1_SALARY_HUB),
    ("청약", CHEONGYAK_MONTHLY, P1_SUBSCRIPTION_BANK),
]

FIXED_P2_ITEMS: list[tuple[str, int, str]] = [
    ("월세·관리·전기 ½→KB공동", COHAB_CONTRIBUTION_P2, HOUSEHOLD_JOINT_BANK),
    ("식비 몫→카카오페이(공동)", FOOD_P2, P1_FOOD_WALLET),
    ("용돈→카카오페이", ALLOWANCE_P2, P2_ALLOWANCE_BANK),
    ("통신", FIXED_PHONE_P2, P2_SALARY_BANK),
    ("건강보험", FIXED_NHIS_P2, P2_SALARY_BANK),
    ("교통", FIXED_TRANSPORT_P2, P2_SALARY_BANK),
]

# 7월 현철 (용돈 0 · 주거 전액+여친고정 · 식비 카카오페이)
FIXED_P1_ITEMS_JULY: list[tuple[str, int, str]] = [
    ("월세·관리·전기 전액→KB공동", JULY_TO_JOINT, HOUSEHOLD_JOINT_BANK),
    ("식비→카카오페이", JULY_TO_FOOD, P1_FOOD_WALLET),
    ("청약", JULY_TO_CHEONGYAK, P1_SUBSCRIPTION_BANK),
    ("KT", FIXED_PHONE_KT, P1_SALARY_HUB),
    ("SKT", FIXED_PHONE_SKT, P1_SALARY_HUB),
    ("통신(여친·현철부담)", FIXED_PHONE_P2, P1_SALARY_HUB),
    ("보험", FIXED_INSURANCE, P1_SALARY_HUB),
    ("구독 합", FIXED_SUBSCRIPTION, P1_SALARY_HUB),
    ("장학금 이자", FIXED_LOAN_SCHOLAR_INTEREST, P1_SALARY_HUB),
    ("카카오 긴급", FIXED_LOAN_KAKAO, P1_SALARY_HUB),
    ("교통(현철)", FIXED_TRANSPORT_P1, P1_SALARY_HUB),
    ("교통(여친·현철부담)", FIXED_TRANSPORT_P2, P1_SALARY_HUB),
]


def p1_net_for_work_month(year: int, month: int) -> int:
    """해당 달 근무분 세후 (수습·일할 반영)."""
    days_in = calendar.monthrange(year, month)[1]
    work_days = [date(year, month, d) for d in range(1, days_in + 1) if date(year, month, d) >= P1_START_DATE]
    if not work_days:
        return 0
    prob_days = sum(1 for d in work_days if d <= P1_PROBATION_END)
    full_days = len(work_days) - prob_days
    if prob_days == days_in and full_days == 0 and (year, month) != (2026, 5):
        return NET_INCOME_P1_PROBATION
    if full_days == days_in and prob_days == 0:
        return NET_INCOME_P1
    return int(prob_days / 30 * NET_INCOME_P1_PROBATION + full_days / 30 * NET_INCOME_P1)


def _work_month_before(pay_year: int, pay_month: int) -> tuple[int, int]:
    if pay_month > 1:
        return pay_year, pay_month - 1
    return pay_year - 1, 12


def household_fixed_costs(p2_net: int, *, july_survival: bool = False) -> int:
    """급여 입금 월 기준 가구 고정비."""
    if july_survival:
        return FIXED_JULY_TOTAL  # 7월: P2 전화·교통 포함, 건보 제외
    if p2_net > 0:
        return FIXED_MONTHLY_TOTAL
    return FIXED_P1_ONLY_TOTAL  # 6월 등 P2 근무·소득 전


def household_net_for_paycheck(pay_year: int, pay_month: int) -> tuple[int, int, int]:
    """급여 입금 월 기준 (p1, p2, 합계). 익월 지급 = 전월 근무분."""
    work_y, work_m = _work_month_before(pay_year, pay_month)
    p1 = p1_net_for_work_month(work_y, work_m) if (work_y, work_m) >= (2026, 5) else 0
    p2 = 0
    if (pay_year, pay_month) >= (P2_FIRST_PAYCHECK_YEAR, P2_FIRST_PAYCHECK_MONTH):
        if (work_y, work_m) >= (P2_WORK_START_DATE.year, P2_WORK_START_DATE.month):
            p2 = p2_net_for_work_month(work_y, work_m)
    return p1, p2, p1 + p2


def calc_allocation(
    p1_net: int,
    p2_net: int,
    *,
    july_survival: bool = False,
) -> dict[str, int | bool]:
    """월급 입금액 기준 자산 배분."""
    fixed = household_fixed_costs(p2_net, july_survival=july_survival)
    if july_survival:
        buffer = p1_net - fixed - FOOD_JULY - ALLOWANCE_P1_JULY - ALLOWANCE_P2_JULY
        return {
            "p1_net": p1_net,
            "p2_net": p2_net,
            "household_net": p1_net + p2_net,
            "save_isa": 0,
            "save_pension": 0,
            "save_visa": 0,
            "save_house_p1": 0,
            "save_house_p2": 0,
            "save_house": 0,
            "save_total": buffer,
            "free_cash": buffer,
            "july_survival": True,
        }

    pension = SAVE_PENSION_P1 if p1_net > 0 else 0
    allow_p1 = ALLOWANCE_P1 if p1_net > 0 else 0
    allow_p2 = ALLOWANCE_P2 if p2_net > 0 else 0
    if p2_net > 0 and p1_net > 0:
        food_p1, food_p2 = food_split_for_save_targets(
            p1_net, p2_net, allow_p1=allow_p1, allow_p2=allow_p2
        )
    elif p1_net > 0:
        food_p1, food_p2 = FOOD_GROCERY, 0
    else:
        food_p1, food_p2 = 0, FOOD_GROCERY

    save_p1 = personal_savings(p1_net, FIXED_P1_TOTAL, food_p1, allow_p1)
    save_p2 = (
        personal_savings(p2_net, FIXED_P2_TOTAL, food_p2, allow_p2) if p2_net > 0 else 0
    )
    cma = SAVE_CMA_EMERGENCY if p1_net > 0 else 0
    isa = min(max(save_p1 - cma, 0), ISA_MONTHLY_CAP) if p1_net > 0 else 0
    house_p1 = max(save_p1 - cma, 0)
    house_p2 = save_p2
    save_total = save_p1 + save_p2
    return {
        "p1_net": p1_net,
        "p2_net": p2_net,
        "household_net": p1_net + p2_net,
        "save_isa": isa,
        "save_pension": pension,
        "save_cma": cma,
        "save_house_p1": house_p1,
        "save_house_p2": house_p2,
        "save_house": house_p1 + house_p2,
        "save_total": save_total,
        "save_p1_total": save_p1,
        "save_p2_total": save_p2,
        "food_p1": food_p1,
        "food_p2": food_p2,
        "free_cash": max(
            p1_net + p2_net - fixed - food_p1 - food_p2 - allow_p1 - allow_p2 - save_total,
            0,
        ),
        "july_survival": False,
    }


def build_payroll_schedule(year: int = 2026) -> list[dict[str, int | str | bool]]:
    """연도별 월급 입금·배분 스케줄."""
    rows: list[dict[str, int | str | bool]] = []
    for month in range(1, 13):
        p1, p2, total = household_net_for_paycheck(year, month)
        if total == 0:
            continue
        work_y, work_m = _work_month_before(year, month)
        july = year == 2026 and month == 7
        alloc = calc_allocation(p1, p2, july_survival=july)
        note_parts: list[str] = []
        if (work_y, work_m) == (2026, 5):
            note_parts.append("5/18 입사·일할")
        elif p1 == NET_INCOME_P1_PROBATION:
            note_parts.append("수습 90%")
        elif NET_INCOME_P1_PROBATION < p1 < NET_INCOME_P1:
            note_parts.append("수습→정규 전환")
        elif p1 == NET_INCOME_P1:
            note_parts.append("정규 연봉")
        if p2 > 0 and month == P2_FIRST_PAYCHECK_MONTH:
            note_parts.append(f"여친 첫 급여({P2_FIRST_PAYCHECK})")
        rows.append(
            {
                "pay_year": year,
                "pay_month": month,
                "work_year": work_y,
                "work_month": work_m,
                "label": f"{year}-{month:02d}",
                "note": " · ".join(note_parts),
                **alloc,
            }
        )
    return rows


PAYROLL_SCHEDULE_2026 = build_payroll_schedule(2026)

# 7월 입금 = 6월 근무분 (수습) · 여친 급여 없음
JULY_NET_INCOME = household_net_for_paycheck(2026, 7)[0]
JULY_BUFFER = int(calc_allocation(JULY_NET_INCOME, 0, july_survival=True)["save_total"])
# 용돈 제외 시 버퍼 · KB 문현철(938002005252755) 잔액 기준 이체
P1_KB_BALANCE = 2_277_161
JULY_BUFFER_NO_ALLOWANCE = JULY_NET_INCOME - FIXED_JULY_TOTAL - FOOD_JULY  # 202,777
JULY_TO_SAMSUNG = (
    P1_KB_BALANCE
    - JULY_TO_JOINT
    - JULY_TO_FOOD
    - FIXED_P1_JULY_ON_KB
    - JULY_TO_CHEONGYAK
)  # 299,081 → 자유입출금
JULY_SAMSUNG_USED = 31_770  # 의류구매 · 주초유 알바용 슬렉스
JULY_SAMSUNG_DAISO = 2_000  # 다이소
JULY_SAMSUNG_TRANSPORT = 5_000  # 교통·주차
JULY_SAMSUNG_ONLINE = 8_374  # 온라인쇼핑
JULY_SAMSUNG_MISC = 7_000  # 생활잡화
JULY_SAMSUNG_PIKPAK = 4_581  # Pickpack · 8월~ CMA 정기
JULY_SAMSUNG_OLIVEYOUNG = 49_970  # 올리브영 · 7/8
JULY_SAMSUNG_SPENT = (
    JULY_SAMSUNG_USED
    + JULY_SAMSUNG_DAISO
    + JULY_SAMSUNG_TRANSPORT
    + JULY_SAMSUNG_ONLINE
    + JULY_SAMSUNG_MISC
    + JULY_SAMSUNG_PIKPAK
    + JULY_SAMSUNG_OLIVEYOUNG
)  # 108,695
P1_VISA_BUFFER_JULY = 299_339  # CMA 내 비자금 (플랜 저축과 별도)
JULY_SAMSUNG_TOTAL = 489_725  # 실잔액 (비자금 포함)
JULY_SAMSUNG_BALANCE = JULY_SAMSUNG_TOTAL - P1_VISA_BUFFER_JULY  # 190,386
JULY_KAKAOPAY_MART = 14_380
JULY_KAKAOPAY_LUNCH = 20_000
JULY_KAKAOPAY_CVS = 2_500
JULY_KAKAOPAY_SNACK = 6_500  # 마트간식
JULY_KAKAOPAY_DINNER = 15_000
JULY_KAKAOPAY_CAFE = 8_000
JULY_KAKAOPAY_CVS2 = 7_000
JULY_KAKAOPAY_MART2 = 35_790
JULY_KAKAOPAY_FOOD3 = 7_800  # 식비 · 7/8
JULY_KAKAOPAY_SPENT = (
    JULY_KAKAOPAY_MART
    + JULY_KAKAOPAY_LUNCH
    + JULY_KAKAOPAY_CVS
    + JULY_KAKAOPAY_SNACK
    + JULY_KAKAOPAY_DINNER
    + JULY_KAKAOPAY_CAFE
    + JULY_KAKAOPAY_CVS2
    + JULY_KAKAOPAY_MART2
    + JULY_KAKAOPAY_FOOD3
)  # 116,970
JULY_KAKAOPAY_BALANCE = JULY_TO_FOOD - JULY_KAKAOPAY_SPENT  # 433,030

# 7월 KB 스타뱅킹 변동비
JULY_KB_CVS = 3_570
JULY_KB_CAFE = 4_000
JULY_KB_MISC = 3_000  # 생활잡화
JULY_KB_DAISO = 21_392
JULY_KB_REFUND = 5_000  # 환불금 · 7/8
JULY_KB_SPENT = JULY_KB_CVS + JULY_KB_CAFE + JULY_KB_MISC + JULY_KB_DAISO  # 31,962
JULY_KB_BALANCE = 486_898 + JULY_KB_REFUND  # 491,898

# ── 7/9 삼성 CMA 자유입출금 정리 이체 (내 계좌 간 이동 · 지출 아님) ──
# CMA 잔액 전액 이동: 10만 → KB 고정비 보강, 나머지 → 토스(현철) 파킹
JULY_CMA_TO_KB = 100_000
JULY_CMA_TO_TOSS = JULY_SAMSUNG_TOTAL - JULY_CMA_TO_KB  # 389,725 (CMA 나머지 전액)

JULY_KB_BALANCE_FINAL = JULY_KB_BALANCE + JULY_CMA_TO_KB  # 591,898
JULY_SAMSUNG_TOTAL_FINAL = (
    JULY_SAMSUNG_TOTAL - JULY_CMA_TO_KB - JULY_CMA_TO_TOSS
)  # 0 · CMA 비움
JULY_TOSS_BALANCE_FINAL = JULY_ALLOWANCE_BALANCE + JULY_CMA_TO_TOSS  # 404,664 (용돈 14,939 + 파킹 389,725)

# 7월 실제 지출 (변동비 · 시트 동기화용) — (날짜, 카테고리, 금액, 메모, 담당자키)
JULY_ACTUAL_EXPENSES: list[tuple[str, str, int, str, str]] = [
    ("2026-07-04", "쇼핑", JULY_SAMSUNG_USED, "의류 · 주초유 알바용 슬렉스 · 삼성CMA", "현철"),
    ("2026-07-04", "생활", JULY_SAMSUNG_DAISO, "다이소 · 삼성CMA", "현철"),
    ("2026-07-04", "식비", JULY_KAKAOPAY_MART, "마트 · 카카오페이", "현철"),
    ("2026-07-04", "식비", JULY_KAKAOPAY_LUNCH, "점심 · 카카오페이", "현철"),
    ("2026-07-04", "식비", JULY_KAKAOPAY_CVS, "편의점 · 카카오페이", "현철"),
    ("2026-07-04", "식비", JULY_KAKAOPAY_SNACK, "마트간식 · 카카오페이", "현철"),
    ("2026-07-06", "식비", JULY_KAKAOPAY_DINNER, "저녁 · 카카오페이", "현철"),
    ("2026-07-06", "식비", JULY_KAKAOPAY_CAFE, "카페 · 카카오페이", "현철"),
    ("2026-07-06", "식비", JULY_KAKAOPAY_CVS2, "편의점 · 카카오페이", "현철"),
    ("2026-07-06", "교통", JULY_SAMSUNG_TRANSPORT, "교통·주차 · 삼성CMA", "현철"),
    ("2026-07-06", "쇼핑", JULY_SAMSUNG_ONLINE, "온라인쇼핑 · 삼성CMA", "현철"),
    ("2026-07-06", "생활", JULY_SAMSUNG_MISC, "생활잡화 · 삼성CMA", "현철"),
    ("2026-07-06", "식비", JULY_KB_CVS, "편의점 · KB스타뱅킹", "현철"),
    ("2026-07-06", "식비", JULY_KB_CAFE, "카페 · KB스타뱅킹", "현철"),
    ("2026-07-06", "생활", JULY_KB_MISC, "생활잡화 · KB스타뱅킹", "현철"),
    ("2026-07-07", "생활", JULY_KB_DAISO, "다이소 · KB", "현철"),
    ("2026-07-07", "식비", JULY_KAKAOPAY_MART2, "마트 · 카카오페이", "현철"),
    ("2026-07-07", "구독", JULY_SAMSUNG_PIKPAK, "Pickpack · 삼성CMA", "현철"),
    ("2026-07-07", "쇼핑", JULY_ALLOWANCE_SHOES, "신발 · 토스용돈", "현철"),
    ("2026-07-08", "식비", JULY_KAKAOPAY_FOOD3, "식비 · 카카오페이", "현철"),
    ("2026-07-08", "쇼핑", JULY_SAMSUNG_OLIVEYOUNG, "올리브영 · 삼성CMA", "현철"),
    ("2026-07-08", "식비", JULY_ALLOWANCE_SNACK, "간식 · 토스용돈", "현철"),
]

# 7월 실제 수입 (시트 동기화용) — (날짜, 유형, 금액, 메모, 담당자키)
JULY_ACTUAL_INCOME: list[tuple[str, str, int, str, str]] = [
    ("2026-07-08", "환불", JULY_KB_REFUND, "환불금 · KB스타뱅킹", "현철"),
]

# ── 10월~ 급여일 자산분배 (급여일 +1일 자동이체 권장) ──
# 각 튜플: (항목, 현철, 여친, 목적계좌) — 8~9월은 수습·전환으로 PAYROLL_SCHEDULE_2026 참고
ASSET_ALLOCATION_AUGUST: list[tuple[str, int, int, str]] = [
    (
        "동거 공동계좌",
        COHAB_P1_TRANSFER,
        COHAB_CONTRIBUTION_P2,
        f"P1/P2→{COHAB_JOINT_ID} ({HOUSEHOLD_JOINT_BANK}) · 상시 {HOUSEHOLD_JOINT_BUFFER:,}원",
    ),
    ("용돈", ALLOWANCE_P1, ALLOWANCE_P2, f"{P1_ALLOWANCE_BANK} / {P2_ALLOWANCE_BANK}"),
    ("ISA", SAVE_ISA, 0, f"{P1_SECURITIES} ISA 서민형 · 청년형 보류(미래적금)"),
    ("연금저축", SAVE_PENSION_P1, 0, f"{P1_SECURITIES} 연금 · 입주 전 0·입주 후 {SAVE_PENSION_P1_AFTER_MOVE_IN:,}"),
    (
        "집마련·비자",
        max(SAVE_HOUSE_P1, 0),
        SAVE_P2_TOSS_MONTHLY,
        f"토스 {SAVE_P2_TOSS_MONTHLY:,} (비자+집) · CMA비상 {SAVE_CMA_EMERGENCY:,}",
    ),
]

# 급여통장(KB)=개인고정·저축이체 · 공동비용=KB 공동
SALARY_IS_FIXED_ACCOUNT = True
FIXED_BUFFER_P1 = PARKING_P1
FIXED_BUFFER_P2 = PARKING_P2
HOUSE_ACCOUNT_P1 = f"{P1_SECURITIES} CMA"
HOUSE_ACCOUNT_P2 = P2_TOSS_BANK

# ── 집 마련 시 자금 인출 가능 여부 (2031~32 목표) ──
HOUSE_FUND_SOURCES: list[tuple[str, str, str, str]] = [
    ("ISA 서민형", "✅ 집마련", "만기 ~2029", "만기까지 적립 → 계약금·이자비과세"),
    ("토스 파킹", "2순위", "2029 이후", f"ISA 초과·입주 잔금 · 월 ~{SAVE_HOUSE // 10_000}만"),
    ("삼성 CMA", "비상금", "T+0", f"월 {SAVE_CMA_EMERGENCY:,} · 집마련 X"),
    ("가계 공동계좌", "△", "비상 시만", f"{HOUSEHOLD_JOINT_BANK} · 월세·식비 버퍼 깨지 않게 최후"),
    ("KB 주거래(개인)", "△", "비상 시만", "개인 고정비·저축 이체용 · 공동비 섞지 않기"),
    ("주택청약 640만", "⚠️ 비권장", "인출 가능하나", "순위·특공 불리"),
    ("연금저축", "입주 후", "세액공제", f"입주 전 0 · 인출 시 공제환수 → 집자금 부적합"),
    ("청년미래적금", "2027 목표", "3년 묶임", f"월 {SAVE_YOUTH_FUTURE_MONTHLY:,} · 청년형 ISA와 중복 불가"),
    ("IRP", "△", "주택구입 사유", f"{P1_SECURITIES} 보유·월 납입 플랜 외"),
    ("~~보통 집마련 통장~~", "❌", "이자 낮음", "사용 안 함"),
]

# ── 통장 구조 (실계좌 · 용돈 보류) ──
BANK_ACCOUNTS: list[dict[str, str | int]] = [
    {
        "id": P1_PERSONAL_HUB_ID,
        "role": "고정비",
        "owner": PERSON1_NAME,
        "institution": P1_SALARY_HUB,
        "account_no": P1_SALARY_ACCT,
        "status": "active",
        "monthly_in": NET_INCOME_P1,
        "purpose": "급여·개인고정 결제·저축 이체 출발",
    },
    {
        "id": COHAB_JOINT_ID,
        "role": "월세·관리비",
        "owner": "공동",
        "institution": HOUSEHOLD_JOINT_BANK,
        "account_no": HOUSEHOLD_JOINT_ACCT,
        "status": "active",
        "monthly_in": FIXED_RENT,
        "purpose": "월세·관리·전기 (식비 X · 7월 현철 전액)",
    },
    {
        "id": "P1-청약",
        "role": "청약",
        "owner": PERSON1_NAME,
        "institution": P1_SUBSCRIPTION_BANK,
        "account_no": P1_CHEONGYAK_ACCT,
        "status": "active",
        "monthly_in": CHEONGYAK_MONTHLY,
        "purpose": f"월 {CHEONGYAK_MONTHLY:,}원 · 잔액 {CHEONGYAK_BALANCE:,}",
    },
    {
        "id": "P1-식비",
        "role": "식비 공동",
        "owner": PERSON1_NAME,
        "institution": P1_FOOD_WALLET,
        "account_no": "",
        "status": "active",
        "monthly_in": FOOD_GROCERY,
        "purpose": "장보기·식비 · 카드 미수령",
    },
    {
        "id": "P1-저축",
        "role": "개인저축",
        "owner": PERSON1_NAME,
        "institution": P1_SECURITIES,
        "account_no": "",
        "status": "active",
        "monthly_in": SAVE_CMA_EMERGENCY,
        "purpose": f"비상금 · 월 {SAVE_CMA_EMERGENCY:,}(15~30만) · ISA {SAVE_ISA:,} 별도",
    },
    {
        "id": "P2-고정비",
        "role": "고정비",
        "owner": PERSON2_NAME,
        "institution": P2_SALARY_BANK,
        "account_no": P2_SALARY_ACCT,
        "status": "from_aug",
        "monthly_in": NET_INCOME_P2,
        "purpose": "급여·개인고정·월세½·식비몫 이체",
    },
    {
        "id": P2_TOSS_ACCOUNT_ID,
        "role": "저축",
        "owner": PERSON2_NAME,
        "institution": P2_SAVE_BANK,
        "account_no": "",
        "status": "from_aug",
        "monthly_in": SAVE_P2_TOSS_MONTHLY,
        "purpose": f"비자+집저축 · 월 {SAVE_P2_TOSS_MONTHLY:,} (비자목표 {SAVE_VISA_BUFFER_P2:,})",
    },
    {
        "id": "P1-용돈",
        "role": "용돈",
        "owner": PERSON1_NAME,
        "institution": P1_ALLOWANCE_BANK,
        "account_no": P1_ALLOWANCE_ACCT,
        "status": "active",
        "monthly_in": JULY_TO_ALLOWANCE_P1,
        "purpose": "통장 개설·등록 · 7월 이체액 0(펀딩 보류)",
    },
    {
        "id": "P2-용돈",
        "role": "용돈",
        "owner": PERSON2_NAME,
        "institution": P2_ALLOWANCE_BANK,
        "account_no": "",
        "status": "active",
        "monthly_in": JULY_TO_ALLOWANCE_P2,
        "purpose": "통장 개설·등록 · 7월 이체액 0(펀딩 보류)",
    },
]

REAL_WALLETS: list[dict[str, str]] = [
    {
        "owner": PERSON1_NAME,
        "institution": P1_SALARY_HUB,
        "account_no": P1_SALARY_ACCT,
        "roles": "고정비·급여",
        "status": "사용중",
    },
    {
        "owner": "공동",
        "institution": HOUSEHOLD_JOINT_BANK,
        "account_no": HOUSEHOLD_JOINT_ACCT,
        "roles": "월세·관리·전기",
        "status": "사용중",
    },
    {
        "owner": PERSON1_NAME,
        "institution": P1_SUBSCRIPTION_BANK,
        "account_no": P1_CHEONGYAK_ACCT,
        "roles": f"청약 월 {CHEONGYAK_MONTHLY // 10_000}만",
        "status": "사용중",
    },
    {
        "owner": PERSON1_NAME,
        "institution": P1_FOOD_WALLET,
        "account_no": "",
        "roles": "식비 공동",
        "status": "사용중",
    },
    {
        "owner": PERSON1_NAME,
        "institution": P1_SECURITIES,
        "account_no": "",
        "roles": "개인저축",
        "status": "사용중",
    },
    {
        "owner": PERSON2_NAME,
        "institution": P2_SALARY_BANK,
        "account_no": P2_SALARY_ACCT,
        "roles": "고정비·급여",
        "status": "8월~",
    },
    {
        "owner": PERSON2_NAME,
        "institution": P2_SAVE_BANK,
        "account_no": "",
        "roles": "저축",
        "status": "8월~",
    },
    {
        "owner": PERSON1_NAME,
        "institution": P1_ALLOWANCE_BANK,
        "account_no": P1_ALLOWANCE_ACCT,
        "roles": "용돈 (금액 보류)",
        "status": "개설·잔액0",
    },
    {
        "owner": PERSON2_NAME,
        "institution": P2_ALLOWANCE_BANK,
        "account_no": "",
        "roles": "용돈 (금액 보류)",
        "status": "개설·잔액0",
    },
]

PAUSED_WALLETS: list[dict[str, str]] = []  # 용돈도 통장 목록에 포함 (이체액만 0)

ROLE_SLOT_COUNT = len(BANK_ACCOUNTS)

# ── 목표 ──
GOAL_NET_WORTH = 150_000_000
GOAL_DATE = "2032-06-30"
CONTRACT_DEPOSIT_TARGET = 50_000_000
MOVE_IN_CASH_TARGET = 100_000_000

# ── 입주 후 대출·관리비 (디딤돌 2.8억·30년·2.6% 가정) ──
MORTGAGE_PRINCIPAL = 280_000_000
MORTGAGE_RATE = 0.026
MORTGAGE_MONTHS = 360
MORTGAGE_MONTHLY_DD = 1_150_000  # 원리금 균등 ~115만
MAINTENANCE_MONTHLY = 150_000  # 관리비·수선 추정
WEDDING_BUDGET_EST = 15_000_000  # 혼인·예식 일회성 (저축에서)

# 허리띠 요약 — 입주·대출 안정 후 생활비 여유 회복 (죽을 때까지 X)
BELT_TIGHT_PEAK_UNTIL = "2031~2032 입주 전후"
BELT_COMFORT_FROM = "2033~2034"  # 카카오 상환 끝·집마련 저축 중단·월 여유 ~60~80만 확보 후

# 입주 후 월 현금흐름 (집마련 저축 중단·월세→대출 전환)
_FIXED_AFTER_MOVE_IN = (
    FIXED_MONTHLY_TOTAL - FIXED_RENT + MORTGAGE_MONTHLY_DD + MAINTENANCE_MONTHLY
)
_SAVE_AFTER_MOVE_IN = SAVE_ISA + SAVE_PENSION_P1_AFTER_MOVE_IN + SAVE_VISA_BUFFER_P2
_FREE_CASH_AFTER_MOVE_IN = (
    NET_INCOME_HOUSEHOLD
    - _FIXED_AFTER_MOVE_IN
    - FOOD_GROCERY
    - ALLOWANCE_P1
    - ALLOWANCE_P2
    - _SAVE_AFTER_MOVE_IN
)
_FIXED_AFTER_KAKAO_PAID = FIXED_MONTHLY_TOTAL - FIXED_LOAN_KAKAO
_FREE_CASH_AFTER_KAKAO = (
    NET_INCOME_HOUSEHOLD
    - _FIXED_AFTER_KAKAO_PAID
    - FOOD_GROCERY
    - ALLOWANCE_P1
    - ALLOWANCE_P2
    - MONTHLY_INVEST_TOTAL
)
FREE_CASH_AFTER_MOVE_IN = _FREE_CASH_AFTER_MOVE_IN
FREE_CASH_AFTER_KAKAO = _FREE_CASH_AFTER_KAKAO
FIXED_AFTER_MOVE_IN = _FIXED_AFTER_MOVE_IN
SAVE_AFTER_MOVE_IN = _SAVE_AFTER_MOVE_IN

# ── 입주 후 · 소득 성장 · 출산 시나리오 ──
INCOME_GROWTH_RATE = 0.04  # 연 4% 세후 가구 소득 성장 (경력·승진 가정)
INCOME_GROWTH_NOTE = "줄지 않는다 전제 — 보수적으로 연 4%"
CHILD_BIRTH_RECOMMENDED = "2033"  # 입주 후 1~2년 적응
CHILD_COST_LIGHT = 500_000  # 어린이집·기저귀 (보조금 반영 후)
CHILD_COST_STANDARD = 700_000
CHILD_COST_HEAVY = 1_000_000  # 민간보육·맞벌이
CHILD_FOOD_EXTRA = 150_000
EMERGENCY_FUND_TARGET = 15_000_000  # 비상금 3~4개월
CHILD_FUND_MONTHLY = 300_000  # 출산 1년 전부터 권장


def household_net_after_years(years: int) -> int:
    """입주 기준 N년 후 세후 가구 소득."""
    return int(NET_INCOME_HOUSEHOLD * (1 + INCOME_GROWTH_RATE) ** years)


def calc_post_move_scenario(
    years_after_move_in: int = 0,
    *,
    child_monthly: int = 0,
    food_extra: int = 0,
    isa_monthly: int | None = None,
    allowance_boost: int = 0,
) -> dict[str, int]:
    """입주 후 월 현금흐름 시나리오."""
    isa = SAVE_ISA if isa_monthly is None else isa_monthly
    pension = SAVE_PENSION_P1_AFTER_MOVE_IN
    save_formal = isa + pension + SAVE_VISA_BUFFER_P2
    net = household_net_after_years(years_after_move_in)
    food = FOOD_GROCERY + food_extra
    allowance = ALLOWANCE_P1 + ALLOWANCE_P2 + allowance_boost
    fixed = _FIXED_AFTER_MOVE_IN
    free_cash = net - fixed - food - allowance - save_formal - child_monthly
    return {
        "years_after_move": years_after_move_in,
        "net_income": net,
        "fixed": fixed,
        "food": food,
        "allowance": allowance,
        "save_isa": isa,
        "save_pension": pension,
        "save_visa": SAVE_VISA_BUFFER_P2,
        "save_formal": save_formal,
        "child": child_monthly,
        "free_cash": free_cash,
        "monthly_wealth": save_formal + max(free_cash, 0),
    }


def mortgage_yearly_breakdown(years: int = 5) -> list[dict[str, int]]:
    """대출 연도별 이자·원금 (원금=집 지분 증가)."""
    r = MORTGAGE_RATE / 12
    bal = MORTGAGE_PRINCIPAL
    pmt = MORTGAGE_MONTHLY_DD
    out: list[dict[str, int]] = []
    for yr in range(1, years + 1):
        interest_y = 0
        principal_y = 0
        for _ in range(12):
            interest = int(bal * r)
            principal = pmt - interest
            interest_y += interest
            principal_y += principal
            bal -= principal
        out.append(
            {
                "year": yr,
                "payment_annual": pmt * 12,
                "interest": interest_y,
                "principal": principal_y,
                "balance_end": int(bal),
            }
        )
    return out


# 입주 직후 vs 지금 저축 비교 행
POST_MOVE_COMPARE: list[tuple[str, int, int, str]] = [
    ("세후 수입", NET_INCOME_HOUSEHOLD, NET_INCOME_HOUSEHOLD, "동일"),
    ("고정비", FIXED_MONTHLY_TOTAL, _FIXED_AFTER_MOVE_IN, "월세→대출+관리"),
    ("식비", FOOD_GROCERY, FOOD_GROCERY, ""),
    ("용돈", ALLOWANCE_P1 + ALLOWANCE_P2, ALLOWANCE_P1 + ALLOWANCE_P2, ""),
    ("집마련 저축", SAVE_HOUSE, 0, "목표 달성·중단"),
    ("ISA", SAVE_ISA, SAVE_ISA, "서민형 유지"),
    ("연금", SAVE_PENSION_P1, SAVE_PENSION_P1_AFTER_MOVE_IN, "입주 전 0 → 입주 후 20만"),
    ("비자·비상", SAVE_VISA_BUFFER_P2, SAVE_VISA_BUFFER_P2, "유지"),
    (
        "남는 돈(여유)",
        0,
        _FREE_CASH_AFTER_MOVE_IN,
        "집마련 슬롯이 여유로 전환",
    ),
    (
        "월 저축+여유 합",
        MONTHLY_INVEST_TOTAL,
        _SAVE_AFTER_MOVE_IN + max(_FREE_CASH_AFTER_MOVE_IN, 0),
        "형태만 바뀜·총액 비슷",
    ),
]

# 여유 배분 권장 (2031~2032)
POST_MOVE_FREE_ALLOCATION: list[tuple[str, int, str]] = [
    ("비상금 적립", 200_000, "15M 채울 때까지"),
    ("외식·여가", 200_000, "스프린트 후 회복"),
    ("자유/버퍼", _FREE_CASH_AFTER_MOVE_IN - 400_000, "아이 통장 전환 전"),
]

CHILD_SCENARIOS: list[dict[str, str | int]] = [
    {
        "id": "S0",
        "name": "무자녀",
        "when": "2031~2032",
        "years_after_move": 0,
        "child_monthly": 0,
        "food_extra": 0,
        "isa_monthly": SAVE_ISA,
        "allowance_boost": 0,
        "note": "입주·대출 적응",
    },
    {
        "id": "S1",
        "name": "무자녀+소득↑",
        "when": "2033",
        "years_after_move": 2,
        "child_monthly": 0,
        "food_extra": 0,
        "isa_monthly": SAVE_ISA,
        "allowance_boost": 100_000,
        "note": f"세후 연{INCOME_GROWTH_RATE:.0%} 성장·용돈+10만",
    },
    {
        "id": "S2",
        "name": "출산(경량)",
        "when": "2033",
        "years_after_move": 2,
        "child_monthly": CHILD_COST_LIGHT,
        "food_extra": CHILD_FOOD_EXTRA,
        "isa_monthly": SAVE_ISA,
        "allowance_boost": 0,
        "note": "어린이집·보조금 반영",
    },
    {
        "id": "S3",
        "name": "출산(표준)",
        "when": "2033",
        "years_after_move": 2,
        "child_monthly": CHILD_COST_STANDARD,
        "food_extra": CHILD_FOOD_EXTRA,
        "isa_monthly": 400_000,
        "allowance_boost": 0,
        "note": "ISA 50→40만",
    },
    {
        "id": "S4",
        "name": "출산(표준)+소득↑",
        "when": "2034",
        "years_after_move": 3,
        "child_monthly": CHILD_COST_STANDARD,
        "food_extra": CHILD_FOOD_EXTRA,
        "isa_monthly": SAVE_ISA,
        "allowance_boost": 0,
        "note": "1년 더 버팀·ISA 유지",
    },
    {
        "id": "S5",
        "name": "출산(헤비)",
        "when": "2033",
        "years_after_move": 2,
        "child_monthly": CHILD_COST_HEAVY,
        "food_extra": CHILD_FOOD_EXTRA,
        "isa_monthly": 300_000,
        "allowance_boost": 0,
        "note": "민간보육·ISA 30만",
    },
]

# 시나리오별 계산 결과 (모듈 로드 시)
CHILD_SCENARIO_RESULTS: list[dict[str, str | int]] = []
for _sc in CHILD_SCENARIOS:
    _r = calc_post_move_scenario(
        int(_sc["years_after_move"]),
        child_monthly=int(_sc["child_monthly"]),
        food_extra=int(_sc["food_extra"]),
        isa_monthly=int(_sc["isa_monthly"]),
        allowance_boost=int(_sc["allowance_boost"]),
    )
    CHILD_SCENARIO_RESULTS.append({**_sc, **_r})

MORTGAGE_YEARLY = mortgage_yearly_breakdown(5)

# 연도별 투영 (2031~2036, 무자녀 → 2033 출산 표준)
POST_MOVE_YEARLY_PROJECTION: list[dict[str, int | str]] = []
for _y in range(6):
    _yr_label = f"2031+{_y}"
    _child = CHILD_COST_STANDARD if _y >= 2 else 0
    _food_x = CHILD_FOOD_EXTRA if _y >= 2 else 0
    _isa = 400_000 if _y >= 2 else SAVE_ISA
    _proj = calc_post_move_scenario(
        _y,
        child_monthly=_child,
        food_extra=_food_x,
        isa_monthly=_isa,
    )
    POST_MOVE_YEARLY_PROJECTION.append({"label": _yr_label, **_proj})

# belt: 5=최대조임 … 1=일상
LIFE_PHASES: list[dict[str, str | int]] = [
    {
        "id": "P0",
        "name": "생존",
        "period": "2026.07",
        "belt": 5,
        "belt_label": "🔴 최대",
        "monthly_free": JULY_BUFFER,
        "summary": "현철 월급만·ISA/연금 보류",
        "tasks": f"고정비 {FIXED_JULY_TOTAL // 10_000}만·식비 55만·여친 소득 0·잔액 CMA",
    },
    {
        "id": "P1",
        "name": "저축전성",
        "period": "2026.08 ~ 2028.상반기",
        "belt": 5,
        "belt_label": "🔴 빡셈",
        "monthly_free": 0,
        "summary": "세후 ~470만 전부 배분·여가 0",
        "tasks": f"집마련 {SAVE_HOUSE // 10_000}만·ISA {SAVE_ISA // 10_000}만·연금 0(입주 후 재개)",
    },
    {
        "id": "P2",
        "name": "혼인·비자",
        "period": "2028.하반기 ~ 2029",
        "belt": 4,
        "belt_label": "🟠 빡셈+이벤트",
        "monthly_free": 0,
        "summary": "혼인신고·예식 일회성 1~2천만",
        "tasks": "D-10→F-6·신혼특공 준비·계약금 5천만 목표",
    },
    {
        "id": "P3",
        "name": "분양·대기",
        "period": "2029 ~ 2031 입주 전",
        "belt": 4,
        "belt_label": "🟠 유지",
        "monthly_free": _FREE_CASH_AFTER_KAKAO,
        "summary": f"카카오 상환 종료(2029.06) → 월 +{FIXED_LOAN_KAKAO:,}원 숨통",
        "tasks": "중도금·집단대출·입주 자금 1억 확보",
    },
    {
        "id": "P4",
        "name": "입주 전환",
        "period": "2031 ~ 2032",
        "belt": 2,
        "belt_label": "🟡 완화 시작",
        "monthly_free": _FREE_CASH_AFTER_MOVE_IN,
        "summary": "집마련 저축 끝·월세→대출·월 여유 회복",
        "tasks": f"디딤돌 {MORTGAGE_PRINCIPAL // 10_000:,}만·CMA+ISA 인출·연금 월{SAVE_PENSION_P1_AFTER_MOVE_IN // 10_000}만 재개",
    },
    {
        "id": "P5",
        "name": "안정",
        "period": "2033 ~ 2035",
        "belt": 2,
        "belt_label": "🟢 숨 쉼",
        "monthly_free": _FREE_CASH_AFTER_MOVE_IN,
        "summary": "용돈·식비·여가 예산 재배분 (월 60~80만 여유)",
        "tasks": "용돈 30~40만·외식·취미 복구·ISA는 선택",
    },
    {
        "id": "P6",
        "name": "중장기",
        "period": "2036~",
        "belt": 1,
        "belt_label": "⚪ 일상",
        "monthly_free": -1,  # 소득 성장 가정·미산출
        "summary": "대출은 갚되 자산은 쌓임·연금은 백그라운드",
        "tasks": "출산·승진·추가 저축은 선택·허리띠 상시 조임 아님",
    },
]

# Google Sheets TODAY() 페이즈 조회용 (시작일 오름차순, C열 MATCH)
LIFE_PHASE_RANGES: list[tuple[str, str, str, str, str, int, str]] = [
    ("P0", "생존", "2026-07-01", "2026-07-31", "🔴 최대", JULY_BUFFER, "7월만·ISA 보류"),
    ("P1", "저축전성", "2026-08-01", "2028-06-30", "🔴 빡셈", 0, f"저축 {MONTHLY_INVEST_TOTAL // 10_000}만·여유 0"),
    ("P2", "혼인·비자", "2028-07-01", "2029-12-31", "🟠 빡셈+이벤트", 0, "예식·F-6"),
    ("P3", "분양·대기", "2030-01-01", "2031-06-30", "🟠 유지", _FREE_CASH_AFTER_KAKAO, "입주 자금 1억"),
    ("P4", "입주 전환", "2031-07-01", "2032-12-31", "🟡 완화", _FREE_CASH_AFTER_MOVE_IN, "집마련 중단"),
    ("P5", "안정", "2033-01-01", "2035-12-31", "🟢 숨 쉼", _FREE_CASH_AFTER_MOVE_IN, "출산·여유 회복"),
    ("P6", "중장기", "2036-01-01", "2040-12-31", "⚪ 일상", -1, "소득 성장·연금 백그라운드"),
]

# ── 세금 ──
PENSION_LIMIT_P1 = 6_000_000
PENSION_TAX_CREDIT_RATE = 0.15
PENSION_PLAN_P1 = SAVE_PENSION_P1 * 12  # 입주 전 0
PENSION_PLAN_P1_AFTER_MOVE_IN = SAVE_PENSION_P1_AFTER_MOVE_IN * 12
ISA_ANNUAL_LIMIT = 20_000_000

# 시트·자산_종목 (실계좌 · 7월 분배 후 목표 잔액 · 용돈 제외)
INVESTMENT_PRODUCTS = [
    {
        "account_type": "CMA",
        "account_name": "문현철-KB고정비",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": P1_SALARY_HUB,
        "qty": 1,
        "price": JULY_KB_BALANCE_FINAL,
        "note": f"{P1_SALARY_ACCT} · 사용 {JULY_KB_SPENT:,} · CMA→KB {JULY_CMA_TO_KB:,}",
    },
    {
        "account_type": "CMA",
        "account_name": "가계-KB공동",
        "owner": "공동",
        "ticker": "",
        "name": HOUSEHOLD_JOINT_BANK,
        "qty": 1,
        "price": JULY_TO_JOINT,
        "note": f"{HOUSEHOLD_JOINT_ACCT} · 월세·관리·전기",
    },
    {
        "account_type": "주택청약",
        "account_name": "문현철-하나청약",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": P1_SUBSCRIPTION_BANK,
        "qty": 1,
        "price": CHEONGYAK_BALANCE + JULY_TO_CHEONGYAK,
        "note": f"{P1_CHEONGYAK_ACCT} · 월 {CHEONGYAK_MONTHLY:,}",
    },
    {
        "account_type": "CMA",
        "account_name": "문현철-카카오페이식비",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": P1_FOOD_WALLET,
        "qty": 1,
        "price": JULY_KAKAOPAY_BALANCE,
        "note": f"식비 · 사용 {JULY_KAKAOPAY_SPENT:,}",
    },
    {
        "account_type": "CMA",
        "account_name": "문현철-삼성자유입출금",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": P1_SECURITIES_JULY,
        "qty": 1,
        "price": JULY_SAMSUNG_TOTAL_FINAL,
        "note": f"7/9 정리 이체 · KB {JULY_CMA_TO_KB:,} + 토스 {JULY_CMA_TO_TOSS:,} · 잔액 0",
    },
    {
        "account_type": "CMA",
        "account_name": "주초유-우리고정비",
        "owner": PERSON2_NAME,
        "ticker": "",
        "name": P2_SALARY_BANK,
        "qty": 1,
        "price": 0,
        "note": f"{P2_SALARY_ACCT} · 8월~",
    },
    {
        "account_type": "CMA",
        "account_name": "주초유-토스저축",
        "owner": PERSON2_NAME,
        "ticker": "",
        "name": P2_SAVE_BANK,
        "qty": 1,
        "price": 0,
        "note": "저축 · 8월~",
    },
    {
        "account_type": "CMA",
        "account_name": "문현철-토스용돈",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": P1_ALLOWANCE_BANK,
        "qty": 1,
        "price": JULY_TOSS_BALANCE_FINAL,
        "note": (
            f"{P1_ALLOWANCE_ACCT} · 용돈 {JULY_ALLOWANCE_BALANCE:,}"
            f" + CMA파킹 {JULY_CMA_TO_TOSS:,}"
        ),
    },
    {
        "account_type": "CMA",
        "account_name": "주초유-카카오페이용돈",
        "owner": PERSON2_NAME,
        "ticker": "",
        "name": P2_ALLOWANCE_BANK,
        "qty": 1,
        "price": JULY_TO_ALLOWANCE_P2,
        "note": "개설 · 7월 이체 0",
    },
]

LIABILITIES = [
    {
        "type": "학자금",
        "name": "장학금(이자만)",
        "principal": LOAN_SCHOLAR_PRINCIPAL,
        "balance": LOAN_SCHOLAR_PRINCIPAL,
        "rate": LOAN_SCHOLAR_RATE * 100,
        "monthly": FIXED_LOAN_SCHOLAR_INTEREST,
        "maturity": "",
        "memo": "이자만 상환",
    },
    {
        "type": "신용대출",
        "name": "카카오긴급생활",
        "principal": LOAN_KAKAO_PRINCIPAL,
        "balance": LOAN_KAKAO_PRINCIPAL,
        "rate": LOAN_KAKAO_RATE * 100,
        "monthly": FIXED_LOAN_KAKAO,
        "maturity": "2029-06-01",
        "memo": "300만·6.7%·36개월·KB 0회",
    },
]

MONTHLY_BUDGET: dict[str, int] = {
    "식비": FOOD_GROCERY,
    "교통": FIXED_TRANSPORT,
    "쇼핑": ALLOWANCE_P1 + ALLOWANCE_P2,
    "고정비": FIXED_RENT + FIXED_ELECTRIC + FIXED_PHONE + FIXED_INSURANCE + FIXED_SUBSCRIPTION + FIXED_NHIS_P2,
    "의료": 0,
    "여가": 0,
    "대출상환": FIXED_LOAN_GENERAL,
    "대출이자": 0,
    "기타": SAVE_VISA_BUFFER_P2,
}

LIABILITY_SAMPLE = LIABILITIES
