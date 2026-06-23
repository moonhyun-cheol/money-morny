"""종합 인생라인 연도·이벤트·자산 투영 (life_plan 기반)."""

from __future__ import annotations

from config.life_plan import (
    BELT_COMFORT_FROM,
    BELT_TIGHT_PEAK_UNTIL,
    CHILD_BIRTH_RECOMMENDED,
    CHILD_COST_STANDARD,
    CHILD_FOOD_EXTRA,
    FIXED_LOAN_KAKAO,
    FREE_CASH_AFTER_MOVE_IN,
    HOUSING_GOAL,
    INCOME_GROWTH_RATE,
    JULY_BUFFER,
    JULY_NET_INCOME,
    MARRIAGE_PLAN,
    MONTHLY_INVEST_TOTAL,
    MORTGAGE_PRINCIPAL,
    MORTGAGE_RATE,
    MORTGAGE_MONTHLY_DD,
    MOVE_IN_CASH_TARGET,
    NET_INCOME_HOUSEHOLD,
    PERSON1_NAME,
    PERSON2_NAME,
    SAVE_HOUSE,
    SAVE_ISA,
    calc_post_move_scenario,
    household_net_after_years,
    mortgage_yearly_breakdown,
)

TIMELINE_START_YEAR = 2026
TIMELINE_END_YEAR = 2040
PERSON1_BIRTH_YEAR = 2000  # 2026년 만 26세
HOME_VALUE_EST = 400_000_000  # 운정 59형 목표가
MOVE_IN_YEAR = 2031
CHEONGYAK_START = 6_400_000
SAVINGS_RATE = 0.025  # 연 2.5% 복리 (CMA·파킹)

# 연도별 페이즈·허리띠
_YEAR_PHASE: dict[int, tuple[str, str, str]] = {
    2026: ("P0~P1", "🔴", "생존→저축전성"),
    2027: ("P1", "🔴", "저축전성"),
    2028: ("P1~P2", "🟠", "저축→혼인"),
    2029: ("P2~P3", "🟠", "혼인·분양"),
    2030: ("P3", "🟠", "분양·대기"),
    2031: ("P3~P4", "🟡", "입주"),
    2032: ("P4", "🟡", "입주 적응"),
    2033: ("P5", "🟢", "안정·출산"),
    2034: ("P5", "🟢", "안정"),
    2035: ("P5", "🟢", "안정"),
}

TIMELINE_EVENTS: dict[int, list[str]] = {
    2026: ["7월 현철 월급만", "8월 여친 첫 급여·자산분배", "저축 루틴 시작"],
    2027: ["D-10 연장(TOPIK6)", "집자금 ~4천만", "비혼 세금최적화"],
    2028: ["혼인신고·F-6", "신혼특공 청약", "예식 1~2천만"],
    2029: ["카카오 대출 종료(6월)", "분양 계약·계약금", "집자금 ~6천만"],
    2030: ["중도금·집단대출", "입주 자금 1억 목표"],
    2031: [f"운정 입주·디딤돌 {MORTGAGE_PRINCIPAL // 10_000:,}만", "집마련 저축 중단", "월 여유 ~63만"],
    2032: ["대출·관리비 적응", "비상금 1,500만"],
    2033: [f"출산 권장({CHILD_BIRTH_RECOMMENDED})", "육아비·ISA 조정"],
    2034: ["소득 성장·여유 회복", "용돈·외식 확대"],
    2035: ["숨통 안정", "추가 저축 선택"],
    2036: ["중장기 일상", "연금 백그라운드"],
    2037: ["대출 원금 상환 누적", "순자산 성장"],
    2040: ["30대 후반 점검", "다음 목표 설정"],
}

QUARTERLY_MILESTONES: list[tuple[str, str, str, str]] = [
    ("2026-Q3", "재무", "7월 생존·CMA", "고정비 123만"),
    ("2026-Q4", "재무", "8월~ 자산분배 고정", "저축 208만/월"),
    ("2027-Q1", "비자", "D-10 연장", "TOPIK 6급"),
    ("2027-Q4", "재무", "집자금 4천만", "청약 유지"),
    ("2028-Q2", "가족", "혼인신고", "F-6 전환"),
    ("2028-Q4", "주택", "신혼특공 청약", "운정 59형"),
    ("2029-Q2", "재무", "카카오 상환 완료", f"+{FIXED_LOAN_KAKAO:,}/월"),
    ("2029-Q3", "주택", "분양 계약", "계약금 5천만"),
    ("2030-Q4", "주택", "입주 준비", "현금 1억"),
    ("2031-Q2", "주택", "입주·이사", "디딤돌 실행"),
    ("2032-Q4", "재무", "비상금 1,500만", "여유 63만 배분"),
    ("2033-Q2", "가족", "출산(권장)", "육아비 70만"),
    ("2034-Q4", "재무", "저축+여유 100만+", "소득 연4%"),
]


def _monthly_net_for_year(year: int) -> int:
    """해당 연도 대표 월 세후 가구 소득."""
    if year == 2026:
        # 7월만 250만, 8~12월 440만
        return int((JULY_NET_INCOME + NET_INCOME_HOUSEHOLD * 5) / 6)
    if year < MOVE_IN_YEAR:
        return int(NET_INCOME_HOUSEHOLD * (1 + INCOME_GROWTH_RATE) ** (year - 2026))
    return household_net_after_years(year - MOVE_IN_YEAR)


def _phase_for_year(year: int) -> tuple[str, str, str]:
    if year in _YEAR_PHASE:
        return _YEAR_PHASE[year]
    if year >= 2036:
        return ("P6", "⚪", "일상")
    return ("P5", "🟢", "안정")


def _simulate_liquid_to_year(end_year: int) -> int:
    """입주 전 유동 자산(청약+집마련+ISA) 연말 잔고."""
    bal = CHEONGYAK_START
    rate = SAVINGS_RATE / 12
    monthly = SAVE_HOUSE + SAVE_ISA
    # 2026.07 ~ end_year.12
    start_y, start_m = 2026, 7
    end_m = 12
    y, m = start_y, start_m
    while (y < end_year) or (y == end_year and m <= end_m):
        if y == 2026 and m == 7:
            bal = bal * (1 + rate) + JULY_BUFFER
        elif (y > 2026) or (y == 2026 and m >= 8):
            bal = bal * (1 + rate) + monthly
        m += 1
        if m > 12:
            m = 1
            y += 1
    return int(bal)


def _mortgage_balance_after_years(years: int) -> int:
  rows = mortgage_yearly_breakdown(years)
  return rows[-1]["balance_end"] if rows else MORTGAGE_PRINCIPAL


def build_yearly_timeline() -> list[dict[str, str | int]]:
    """2026~2040 연도별 인생라인 행."""
    rows: list[dict[str, str | int]] = []
    pre_move_liquid_at_2030 = _simulate_liquid_to_year(MOVE_IN_YEAR - 1)

    for year in range(TIMELINE_START_YEAR, TIMELINE_END_YEAR + 1):
        phase_id, belt, phase_name = _phase_for_year(year)
        events = TIMELINE_EVENTS.get(year, [])
        events_str = " · ".join(events) if events else ""
        age = year - PERSON1_BIRTH_YEAR

        if year < MOVE_IN_YEAR:
            monthly_net = _monthly_net_for_year(year)
            if year == 2026:
                monthly_save = int(JULY_BUFFER)  # 연말 기준 대표값(7월)
                monthly_free = JULY_BUFFER
            else:
                monthly_save = MONTHLY_INVEST_TOTAL
                monthly_free = 0
            liquid = _simulate_liquid_to_year(year)
            rows.append(
                {
                    "year": year,
                    "age": age,
                    "phase_id": phase_id,
                    "belt": belt,
                    "phase_name": phase_name,
                    "monthly_net": monthly_net,
                    "annual_net": monthly_net * 12,
                    "monthly_save": monthly_save,
                    "monthly_free": monthly_free,
                    "liquid_assets": liquid,
                    "home_equity": 0,
                    "mortgage": 0,
                    "net_worth": liquid,
                    "events": events_str,
                    "housing": "월세",
                    "family": _family_note(year),
                }
            )
            continue

        years_in = year - MOVE_IN_YEAR
        child = CHILD_COST_STANDARD if year >= 2033 else 0
        food_x = CHILD_FOOD_EXTRA if year >= 2033 else 0
        isa = 400_000 if year >= 2033 else SAVE_ISA
        sc = calc_post_move_scenario(
            years_in,
            child_monthly=child,
            food_extra=food_x,
            isa_monthly=isa,
        )
        monthly_net = int(sc["net_income"])
        liquid = (
            max(pre_move_liquid_at_2030 - MOVE_IN_CASH_TARGET, 0)
            if years_in == 0
            else _liquid_after_move_in(years_in)
        )
        mortgage_bal = _mortgage_balance_after_years(years_in + 1)
        home_equity = HOME_VALUE_EST - mortgage_bal
        rows.append(
            {
                "year": year,
                "age": age,
                "phase_id": phase_id,
                "belt": belt,
                "phase_name": phase_name,
                "monthly_net": monthly_net,
                "annual_net": monthly_net * 12,
                "monthly_save": int(sc["monthly_wealth"]),
                "monthly_free": int(sc["free_cash"]),
                "liquid_assets": liquid,
                "home_equity": home_equity,
                "mortgage": mortgage_bal,
                "net_worth": home_equity + liquid,
                "events": events_str,
                "housing": "자가·대출",
                "family": _family_note(year),
            }
        )

    return rows


def _liquid_after_move_in(years_after: int) -> int:
    """입주 후 유동자산(인출 잔여 + 매월 저축 누적)."""
    remain = max(_simulate_liquid_to_year(MOVE_IN_YEAR - 1) - MOVE_IN_CASH_TARGET, 0)
    rate = SAVINGS_RATE / 12
    bal = remain
    for y in range(1, years_after + 1):
        child = CHILD_COST_STANDARD if y + MOVE_IN_YEAR >= 2033 else 0
        food_x = CHILD_FOOD_EXTRA if y + MOVE_IN_YEAR >= 2033 else 0
        isa = 400_000 if y + MOVE_IN_YEAR >= 2033 else SAVE_ISA
        sc = calc_post_move_scenario(y, child_monthly=child, food_extra=food_x, isa_monthly=isa)
        monthly_add = max(int(sc["monthly_wealth"]), 0)
        for _ in range(12):
            bal = bal * (1 + rate) + monthly_add
    return int(bal)


def _family_note(year: int) -> str:
    if year < 2027:
        return "D-10·구직"
    if year < 2028:
        return "D-10 연장"
    if year < 2033:
        return "F-6·2인"
    if year == 2033:
        return "출산(권장)"
    return "3인 가구"


def dashboard_summary() -> list[tuple[str, str]]:
    return [
        ("가구", f"{PERSON1_NAME} + {PERSON2_NAME}"),
        ("혼인", MARRIAGE_PLAN),
        ("주택", HOUSING_GOAL),
        ("허리띠 최대", BELT_TIGHT_PEAK_UNTIL),
        ("숨통 트임", BELT_COMFORT_FROM),
        ("입주 목표", f"{MOVE_IN_YEAR}년 · 현금 {MOVE_IN_CASH_TARGET // 10_000:,}만"),
        ("출산 권장", CHILD_BIRTH_RECOMMENDED),
        ("소득 가정", f"연 {INCOME_GROWTH_RATE:.0%} 성장"),
        ("입주 후 여유", f"월 {FREE_CASH_AFTER_MOVE_IN:,}원"),
        ("Google 연동", "sheets/종합인생라인.xlsx → Drive 업로드"),
    ]
