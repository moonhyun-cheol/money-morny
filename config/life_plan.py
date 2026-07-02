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
NET_INCOME_P2 = p2_net_for_work_month(2026, 10)
ANNUAL_INCOME_P2 = sum(p2_gross_for_work_month(2026, m) for m in range(1, 13)) // 10_000
ANNUAL_INCOME_HOUSEHOLD = ANNUAL_INCOME_P1 + ANNUAL_INCOME_P2
NET_INCOME_HOUSEHOLD = NET_INCOME_P1 + NET_INCOME_P2  # 10월~ 정상 가구 세후

# ── [1] 주거·공과 ──
FIXED_RENT = 600_000  # 월세+관리비
FIXED_ELECTRIC = 50_000
FIXED_SHARED = FIXED_RENT + FIXED_ELECTRIC  # 650,000
FIXED_SHARED_HALF = FIXED_SHARED // 2  # 325,000

# ── [2] 통신 ──
FIXED_PHONE_KT = 2_890
FIXED_PHONE_SKT = 34_000
FIXED_PHONE_P2 = 20_000  # 여친
FIXED_PHONE = FIXED_PHONE_KT + FIXED_PHONE_SKT + FIXED_PHONE_P2

# ── [3] 보험 (KB 2026-06-04 첫 납부 138,290) ──
FIXED_INSURANCE = 138_290

# ── [4] 구독 (원/월) ──
SUB_ICLOUD = 5_000  # 실청구 ~4,400 · 카카오페이 5,000 가정
SUB_COUPANG = 7_890
SUB_LIMBUS = 9_900 + 4_900  # 14,800
SUB_SPOTIFY = 11_990
SUB_YOUTUBE = 10_900  # 구 14,900(토스·21일) → 2026-05~ 갈아탐
SUB_CURSOR_KRW = 120_000  # Cursor Pro+ 구독 (2026-06~ · 월 12만)
FIXED_SUBSCRIPTION = (
    SUB_ICLOUD + SUB_COUPANG + SUB_LIMBUS + SUB_SPOTIFY + SUB_YOUTUBE + SUB_CURSOR_KRW
)  # 78,580

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

# ── 인당 고정비 (공동 ½ + 전용) ──
FIXED_P1_EXCLUSIVE = (
    FIXED_PHONE_KT
    + FIXED_PHONE_SKT
    + FIXED_INSURANCE
    + FIXED_SUBSCRIPTION
    + FIXED_LOAN_SCHOLAR_INTEREST
    + FIXED_LOAN_KAKAO
    + FIXED_TRANSPORT_P1
)  # 519,492
FIXED_P2_EXCLUSIVE = FIXED_PHONE_P2 + FIXED_NHIS_P2 + FIXED_TRANSPORT_P2  # 165,778 (8월~)
FIXED_P1_TOTAL = FIXED_P1_EXCLUSIVE + FIXED_SHARED_HALF  # 844,492
FIXED_P2_TOTAL = FIXED_P2_EXCLUSIVE + FIXED_SHARED_HALF  # 490,778

# 7월: 여친 소득 없음 · 전화·교통 등 P2 고정비 포함 (건보는 8월 급여부터)
FIXED_JULY_TOTAL = FIXED_MONTHLY_TOTAL - FIXED_NHIS_P2
FIXED_P1_ONLY_TOTAL = FIXED_MONTHLY_TOTAL - FIXED_P2_EXCLUSIVE  # 6월 등 P2 근무 전

# 고정비 항목 — (항목명, 월금액, 담당, 메모)
FIXED_COST_ITEMS: list[tuple[str, int, str, str]] = [
    ("월세+관리비", FIXED_RENT, "공동", ""),
    ("전기", FIXED_ELECTRIC, "공동", "추정 5만"),
    ("KT", FIXED_PHONE_KT, PERSON1_NAME, "FBS ~23일"),
    ("SKT", FIXED_PHONE_SKT, PERSON1_NAME, "지로 ~22일"),
    ("통신(여친)", FIXED_PHONE_P2, PERSON2_NAME, ""),
    ("보험", FIXED_INSURANCE, PERSON1_NAME, "2026-06-04 KB카드"),
    ("iCloud", SUB_ICLOUD, PERSON1_NAME, "카카오 ~5천"),
    ("쿠팡 와우", SUB_COUPANG, PERSON1_NAME, "27일"),
    ("림버스컴퍼니", SUB_LIMBUS, PERSON1_NAME, "9900+4900"),
    ("Spotify", SUB_SPOTIFY, PERSON1_NAME, "3일"),
    ("YouTube Premium", SUB_YOUTUBE, PERSON1_NAME, "28일 전후"),
    ("Cursor", SUB_CURSOR_KRW, PERSON1_NAME, "Pro+ 12만/월"),
    ("장학금 이자", FIXED_LOAN_SCHOLAR_INTEREST, PERSON1_NAME, "27일 ~2,887"),
    ("카카오 긴급생활", FIXED_LOAN_KAKAO, PERSON1_NAME, "KB 0회·카뱅 확인"),
    ("건강보험(여친)", FIXED_NHIS_P2, PERSON2_NAME, "8월 첫 급여~ 직장가입"),
    ("교통(현철)", FIXED_TRANSPORT_P1, PERSON1_NAME, "정가 왕복 9800×22"),
    ("교통(여친)", FIXED_TRANSPORT_P2, PERSON2_NAME, f"{P2_WORK_SCHEDULE}·정가 3500×22"),
]

# ── 식비·용돈 ──
FOOD_GROCERY = 750_000
ALLOWANCE_P1 = 150_000
ALLOWANCE_P2 = 100_000

# 7월 축소 (현철 월급만)
FOOD_JULY = 550_000
ALLOWANCE_P1_JULY = 100_000
ALLOWANCE_P2_JULY = 0

# ── 투자·저축 (10월~ 정상, 세후 가구 ~470만 기준) ──
SAVE_YOUTH_LEAP = 0
SAVE_ISA = 500_000
SAVE_PENSION_P1 = 200_000
SAVE_VISA_BUFFER_P2 = 50_000
SAVE_SUBSCRIPTION_MIN = 0

_remainder = (
    NET_INCOME_HOUSEHOLD - FIXED_MONTHLY_TOTAL - FOOD_GROCERY - ALLOWANCE_P1 - ALLOWANCE_P2
)
SAVE_HOUSE = _remainder - SAVE_ISA - SAVE_PENSION_P1 - SAVE_VISA_BUFFER_P2

MONTHLY_INVEST_TOTAL = SAVE_ISA + SAVE_HOUSE + SAVE_PENSION_P1 + SAVE_VISA_BUFFER_P2

# 8월~ 식비·집마련 (소득 비율 배분, 파킹은 실액 기준)
FOOD_P1 = round(FOOD_GROCERY * NET_INCOME_P1 / NET_INCOME_HOUSEHOLD)  # 426,136
FOOD_P2 = FOOD_GROCERY - FOOD_P1  # 323,864

SAVE_HOUSE_P1 = (
    NET_INCOME_P1
    - FIXED_P1_TOTAL
    - FOOD_P1
    - ALLOWANCE_P1
    - SAVE_ISA
    - SAVE_PENSION_P1
)
SAVE_HOUSE_P2 = (
    NET_INCOME_P2
    - FIXED_P2_TOTAL
    - FOOD_P2
    - ALLOWANCE_P2
    - SAVE_VISA_BUFFER_P2
)

# ── 동거 공동계좌 (월세·전기·장보기) · 현철 KB = 급여·개인고정비 ──
HOUSEHOLD_JOINT_BANK = "KB 공동"
COHAB_JOINT_ID = "가계공동"
COHAB_HUB_ID = COHAB_JOINT_ID
COHAB_HUB_INSTITUTION = HOUSEHOLD_JOINT_BANK
P1_PERSONAL_HUB_ID = "P1-급여"
# ── 실제 보유 금융사 (2026-06 · 물리 통장 기준) ──
P1_SALARY_HUB = "KB 주거래"  # 급여 입금 · 개인 고정비 · 저축 이체만
P1_ALLOWANCE_BANK = "토스"
P1_SECURITIES = "삼성증권"  # CMA · ISA · 연금 · IRP (증권사 1곳)
P1_SUBSCRIPTION_BANK = "기존 청약"
CHEONGYAK_BALANCE = 6_400_000  # 청약 잔액 640만
P2_SALARY_BANK = "알바 급여 은행"  # 기존
P2_ALLOWANCE_BANK = "토스"  # 용돈 전용 (토스뱅크와 분리)
P2_TOSS_BANK = "토스뱅크"  # 신규 개설 · 파킹(집+비자)만
PHYSICAL_ACCOUNT_COUNT = 7  # 현철 KB+KB공동+토스+삼성 + 여친 알바+토스+토스뱅
ACCOUNTS_TO_OPEN: list[dict[str, str]] = [
    {
        "owner": "공동",
        "institution": HOUSEHOLD_JOINT_BANK,
        "purpose": "월세·전기·장보기 · 동거분담금 입금",
        "note": "공동명의(또는 연동) · 개설 시 둘 다 방문 · 월 지출 ~140만",
    },
    {
        "owner": PERSON2_NAME,
        "institution": P2_TOSS_BANK,
        "purpose": "파킹 통장 · 집마련+비자 자동이체 (~132만/월)",
        "note": "ARC·본인 명의 휴대폰 · 개설 후 한도 해제",
    },
]
COHAB_P1_TRANSFER = FIXED_SHARED_HALF + FOOD_P1
COHAB_P1_TRANSFER_JULY = FIXED_SHARED + FOOD_JULY
COHAB_CONTRIBUTION_P2 = FIXED_SHARED_HALF + FOOD_P2
HOUSEHOLD_JOINT_OUTFLOW = FIXED_SHARED + FOOD_GROCERY
HOUSEHOLD_JOINT_BUFFER = HOUSEHOLD_JOINT_OUTFLOW
HOUSEHOLD_JOINT_BUFFER_JULY = FIXED_SHARED + FOOD_JULY
HOUSEHOLD_HUB_BUFFER = HOUSEHOLD_JOINT_BUFFER  # legacy alias
PARKING_P1 = FIXED_P1_EXCLUSIVE
PARKING_P2 = FIXED_P2_EXCLUSIVE + 50_000
P2_TOSS_ACCOUNT_ID = "P2-토스파킹"
SAVE_P2_TOSS_MONTHLY = SAVE_HOUSE_P2 + SAVE_VISA_BUFFER_P2

HOUSEHOLD_JOINT_ITEMS: list[tuple[str, int, str]] = [
    ("월세+관리비", FIXED_RENT, HOUSEHOLD_JOINT_BANK),
    ("전기", FIXED_ELECTRIC, HOUSEHOLD_JOINT_BANK),
    ("장보기", FOOD_GROCERY, HOUSEHOLD_JOINT_BANK),
]

FIXED_P1_ITEMS: list[tuple[str, int, str]] = [
    ("월세+전기 ½→공동", FIXED_SHARED_HALF, HOUSEHOLD_JOINT_BANK),
    ("식비 몫→공동", FOOD_P1, HOUSEHOLD_JOINT_BANK),
    ("KT", FIXED_PHONE_KT, "FBS"),
    ("SKT", FIXED_PHONE_SKT, "지로"),
    ("보험", FIXED_INSURANCE, "KB카드"),
    ("iCloud", SUB_ICLOUD, "카카오"),
    ("쿠팡 와우", SUB_COUPANG, ""),
    ("림버스", SUB_LIMBUS, ""),
    ("Spotify", SUB_SPOTIFY, "3일"),
    ("YouTube", SUB_YOUTUBE, ""),
    ("Cursor", SUB_CURSOR_KRW, ""),
    ("장학금 이자", FIXED_LOAN_SCHOLAR_INTEREST, ""),
    ("카카오 긴급", FIXED_LOAN_KAKAO, "카뱅"),
    ("교통", FIXED_TRANSPORT_P1, "정가"),
]

FIXED_P2_ITEMS: list[tuple[str, int, str]] = [
    ("월세+전기 ½→공동", FIXED_SHARED_HALF, HOUSEHOLD_JOINT_BANK),
    ("식비 몫→공동", FOOD_P2, HOUSEHOLD_JOINT_BANK),
    ("통신", FIXED_PHONE_P2, ""),
    ("건강보험", FIXED_NHIS_P2, "8월~"),
    ("교통", FIXED_TRANSPORT_P2, f"{P2_WORK_SCHEDULE}·정가"),
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

    isa = SAVE_ISA if p1_net > 0 else 0
    pension = SAVE_PENSION_P1 if p1_net > 0 else 0
    visa = SAVE_VISA_BUFFER_P2 if p2_net > 0 else 0
    allow_p1 = ALLOWANCE_P1 if p1_net > 0 else 0
    allow_p2 = ALLOWANCE_P2 if p2_net > 0 else 0
    if p2_net > 0 and p1_net > 0:
        food_p1 = round(FOOD_GROCERY * p1_net / (p1_net + p2_net))
        food_p2 = FOOD_GROCERY - food_p1
    elif p1_net > 0:
        food_p1, food_p2 = FOOD_GROCERY, 0
    else:
        food_p1, food_p2 = 0, FOOD_GROCERY

    house_p1 = max(p1_net - FIXED_P1_TOTAL - food_p1 - allow_p1 - isa - pension, 0)
    house_p2 = max(p2_net - FIXED_P2_TOTAL - food_p2 - allow_p2 - visa, 0) if p2_net > 0 else 0
    save_total = isa + pension + visa + house_p1 + house_p2
    return {
        "p1_net": p1_net,
        "p2_net": p2_net,
        "household_net": p1_net + p2_net,
        "save_isa": isa,
        "save_pension": pension,
        "save_visa": visa,
        "save_house_p1": house_p1,
        "save_house_p2": house_p2,
        "save_house": house_p1 + house_p2,
        "save_total": save_total,
        "free_cash": max(
            p1_net + p2_net - fixed - FOOD_GROCERY - allow_p1 - allow_p2 - save_total,
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
    ("ISA", SAVE_ISA, 0, f"{P1_SECURITIES} ISA"),
    ("연금저축", SAVE_PENSION_P1, 0, f"{P1_SECURITIES} 연금"),
    (
        "집마련·비자",
        SAVE_HOUSE_P1,
        SAVE_P2_TOSS_MONTHLY,
        f"{P1_SECURITIES} CMA / {P2_TOSS_BANK} (집 {SAVE_HOUSE_P2:,}+비자 {SAVE_VISA_BUFFER_P2:,})",
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
    ("집마련 CMA·파킹", "✅ 1순위", "자유·T+0~1", "삼성CMA(현철)+토스파킹(여친·비자5만 포함)·보통예금 대신"),
    ("ISA 서민형", "✅ 2순위", "만기 전 원금 인출", "2029 계약금·이자비과세"),
    ("가계 공동계좌", "△", "비상 시만", f"{HOUSEHOLD_JOINT_BANK} · 월세·식비 버퍼 깨지 않게 최후"),
    ("KB 주거래(개인)", "△", "비상 시만", "개인 고정비·저축 이체용 · 공동비 섞지 않기"),
    ("주택청약 640만", "⚠️ 비권장", "인출 가능하나", "순위·특공 불리"),
    ("연금저축", "△ 최후", "부분 인출", "16.5% + 세액공제 환수"),
    ("IRP", "△", "주택구입 사유", f"{P1_SECURITIES} 보유·월 납입 플랜 외"),
    ("~~보통 집마련 통장~~", "❌", "이자 낮음", "사용 안 함"),
]

# ── 통장 구조 (역할 10슬롯 · 물리 통장 7개) ──
BANK_ACCOUNTS: list[dict[str, str | int]] = [
    {
        "id": COHAB_JOINT_ID,
        "role": "동거·공동",
        "owner": "공동",
        "institution": HOUSEHOLD_JOINT_BANK,
        "monthly_in": COHAB_P1_TRANSFER + COHAB_CONTRIBUTION_P2,
        "purpose": (
            f"월세·전기·장보기 결제 · 상시 {HOUSEHOLD_JOINT_BUFFER:,}원 "
            f"(현철 {COHAB_P1_TRANSFER:,} + 여친 {COHAB_CONTRIBUTION_P2:,})"
        ),
    },
    {
        "id": P1_PERSONAL_HUB_ID,
        "role": "급여·개인고정비",
        "owner": PERSON1_NAME,
        "institution": P1_SALARY_HUB,
        "monthly_in": NET_INCOME_P1,
        "purpose": (
            f"급여 → 공동 {COHAB_P1_TRANSFER:,} · 저축 이체 · 개인고정 "
            f"상시 {FIXED_P1_EXCLUSIVE:,}원"
        ),
    },
    {
        "id": "P1-집마련",
        "role": "집마련",
        "owner": PERSON1_NAME,
        "institution": HOUSE_ACCOUNT_P1,
        "monthly_in": SAVE_HOUSE_P1,
        "purpose": "CMA RP·MMF · 7월 버퍼도 여기",
    },
    {
        "id": "P1-용돈",
        "role": "용돈",
        "owner": PERSON1_NAME,
        "institution": P1_ALLOWANCE_BANK,
        "monthly_in": ALLOWANCE_P1,
        "purpose": "개인 소비만",
    },
    {
        "id": "P1-ISA",
        "role": "저축",
        "owner": PERSON1_NAME,
        "institution": f"{P1_SECURITIES} ISA",
        "monthly_in": SAVE_ISA,
        "purpose": "집값 2순위·2029 계약금",
    },
    {
        "id": "P1-연금",
        "role": "저축",
        "owner": PERSON1_NAME,
        "institution": f"{P1_SECURITIES} 연금",
        "monthly_in": SAVE_PENSION_P1,
        "purpose": "세액공제만·집값 X",
    },
    {
        "id": "P1-청약",
        "role": "저축",
        "owner": PERSON1_NAME,
        "institution": P1_SUBSCRIPTION_BANK,
        "monthly_in": 20_000,
        "purpose": f"청약 {CHEONGYAK_BALANCE:,}원 유지",
    },
    {
        "id": "P2-급여·본인고정비",
        "role": "급여·본인고정비",
        "owner": PERSON2_NAME,
        "institution": P2_SALARY_BANK,
        "monthly_in": NET_INCOME_P2,
        "purpose": (
            f"급여+건보·교통·통신 · 동거분담 {COHAB_CONTRIBUTION_P2:,}원→{COHAB_JOINT_ID} · "
            f"상시 {FIXED_BUFFER_P2:,}원"
        ),
    },
    {
        "id": P2_TOSS_ACCOUNT_ID,
        "role": "집마련·비자",
        "owner": PERSON2_NAME,
        "institution": P2_TOSS_BANK,
        "monthly_in": SAVE_P2_TOSS_MONTHLY,
        "purpose": (
            f"파킹 집마련 {SAVE_HOUSE_P2:,} + 비자 {SAVE_VISA_BUFFER_P2:,} · "
            "2031 입주 후 집마련 중단"
        ),
    },
    {
        "id": "P2-용돈",
        "role": "용돈",
        "owner": PERSON2_NAME,
        "institution": P2_ALLOWANCE_BANK,
        "monthly_in": ALLOWANCE_P2,
        "purpose": "용돈 전용 · 토스뱅크(파킹)와 분리",
    },
]

REAL_WALLETS: list[dict[str, str]] = [
    {
        "owner": "공동",
        "institution": HOUSEHOLD_JOINT_BANK,
        "roles": "월세·전기·장보기 · ★신규 개설",
    },
    {
        "owner": PERSON1_NAME,
        "institution": P1_SALARY_HUB,
        "roles": "급여·개인고정비·저축이체",
    },
    {"owner": PERSON1_NAME, "institution": P1_ALLOWANCE_BANK, "roles": "용돈"},
    {
        "owner": PERSON1_NAME,
        "institution": P1_SECURITIES,
        "roles": "CMA(집) · ISA · 연금 · IRP",
    },
    {"owner": PERSON1_NAME, "institution": P1_SUBSCRIPTION_BANK, "roles": "청약 2만/월"},
    {
        "owner": PERSON2_NAME,
        "institution": P2_SALARY_BANK,
        "roles": "급여·본인고정비·동거분담→공동",
    },
    {"owner": PERSON2_NAME, "institution": P2_ALLOWANCE_BANK, "roles": "용돈 10만"},
    {
        "owner": PERSON2_NAME,
        "institution": P2_TOSS_BANK,
        "roles": "파킹(집+비자) · ★신규 개설",
    },
]

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
_SAVE_AFTER_MOVE_IN = SAVE_ISA + SAVE_PENSION_P1 + SAVE_VISA_BUFFER_P2
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
    save_formal = isa + SAVE_PENSION_P1 + SAVE_VISA_BUFFER_P2
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
        "save_pension": SAVE_PENSION_P1,
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
    ("ISA", SAVE_ISA, SAVE_ISA, "유지"),
    ("연금", SAVE_PENSION_P1, SAVE_PENSION_P1, "유지"),
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
        "tasks": f"집마련 {SAVE_HOUSE // 10_000}만·ISA 50·연금 20·용돈 25만 유지",
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
        "tasks": f"디딤돌 {MORTGAGE_PRINCIPAL // 10_000:,}만·CMA+ISA 인출·이사",
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
PENSION_PLAN_P1 = 2_400_000
ISA_ANNUAL_LIMIT = 20_000_000

INVESTMENT_PRODUCTS = [
    {
        "account_type": "ISA",
        "account_name": "현철-ISA서민형",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": "MMF/예금",
        "qty": 1,
        "price": 0,
        "note": "월 50만·8월~",
    },
    {
        "account_type": "주택청약",
        "account_name": "현철-청약통장",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": "주택청약종합저축",
        "qty": 1,
        "price": 6_400_000,
        "note": "640만 유지",
    },
    {
        "account_type": "연금저축",
        "account_name": "현철-연금저축",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": "연금저축",
        "qty": 1,
        "price": 0,
        "note": "월 20만·8월~",
    },
    {
        "account_type": "CMA",
        "account_name": "현철-집마련CMA",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": "삼성증권 CMA",
        "qty": 1,
        "price": 0,
        "note": f"월 {SAVE_HOUSE_P1 // 10_000}만·RP이자",
    },
    {
        "account_type": "현금",
        "account_name": "현철-급여고정비",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": "KB 주거래",
        "qty": 1,
        "price": 0,
        "note": "급여+고정비·상시 85만",
    },
    {
        "account_type": "현금",
        "account_name": "현철-용돈",
        "owner": PERSON1_NAME,
        "ticker": "",
        "name": "KB 용돈",
        "qty": 1,
        "price": 0,
        "note": "월 15만",
    },
    {
        "account_type": "CMA",
        "account_name": "여친-집마련파킹",
        "owner": PERSON2_NAME,
        "ticker": "",
        "name": "토스뱅크 파킹",
        "qty": 1,
        "price": 0,
        "note": f"월 {SAVE_HOUSE_P2 // 10_000}만",
    },
    {
        "account_type": "현금",
        "account_name": "여친-비자비상",
        "owner": PERSON2_NAME,
        "ticker": "",
        "name": "비자·비상",
        "qty": 1,
        "price": 0,
        "note": "TOPIK6·월 5만",
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
