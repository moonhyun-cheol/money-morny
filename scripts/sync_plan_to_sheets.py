#!/usr/bin/env python3
"""life_plan 고정비·7월 플랜을 기존 재무관리 Google 시트 전 탭에 반영."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CONFIG_DIR = ROOT / "config"
DEFAULT_SHEET_ID = "1gbOP9awkXF0v8ymqP8rP5FEtsyEOlS5TG3oNMB6srd0"

# 시트에 이미 쓰는 실명 (설정 탭과 맞춤)
SHEET_P1 = "문현철"
SHEET_P2 = "주초유"
NAME_MAP = {"현철": SHEET_P1, "여친": SHEET_P2, "공동": "공동"}


def _owner(who: str) -> str:
    return NAME_MAP.get(who, who)


def _category(name: str) -> str:
    if name.startswith("교통"):
        return "교통"
    if "장학금" in name:
        return "대출이자"
    if "카카오" in name:
        return "대출상환"
    return "고정비"


def july_budget() -> dict[str, int]:
    from config.life_plan import (
        ALLOWANCE_P1_JULY,
        ALLOWANCE_P2_JULY,
        FIXED_ELECTRIC,
        FIXED_INSURANCE,
        FIXED_LOAN_KAKAO,
        FIXED_LOAN_SCHOLAR_INTEREST,
        FIXED_PHONE,
        FIXED_RENT,
        FIXED_SUBSCRIPTION,
        FIXED_TRANSPORT,
        FOOD_JULY,
    )

    return {
        "식비": FOOD_JULY,
        "교통": FIXED_TRANSPORT,
        "쇼핑": ALLOWANCE_P1_JULY + ALLOWANCE_P2_JULY,
        "고정비": (
            FIXED_RENT
            + FIXED_ELECTRIC
            + FIXED_PHONE
            + FIXED_INSURANCE
            + FIXED_SUBSCRIPTION
        ),
        "의료": 0,
        "여가": 0,
        "대출상환": FIXED_LOAN_KAKAO,
        "대출이자": FIXED_LOAN_SCHOLAR_INTEREST,
        "기타": 0,
    }


def build_expense_rows() -> list[list]:
    from config.life_plan import (
        ALLOWANCE_P1_JULY,
        FIXED_COST_ITEMS,
        FOOD_JULY,
        JULY_ACTUAL_EXPENSES,
        PERSON1_NAME,
    )

    rows: list[list] = [["날짜", "카테고리", "금액", "메모", "담당자"]]
    for name, amt, who, memo in FIXED_COST_ITEMS:
        if name.startswith("건강보험"):
            continue
        note = f"{name}" + (f" · {memo}" if memo else "") + " · 7월계획"
        rows.append(["2026-07-01", _category(name), amt, note, _owner(who)])

    rows.append(
        [
            "2026-07-01",
            "식비",
            FOOD_JULY,
            "식비→카카오페이(현철) · 7월계획",
            _owner(PERSON1_NAME),
        ]
    )
    rows.append(
        [
            "2026-07-01",
            "쇼핑",
            ALLOWANCE_P1_JULY,
            "용돈(현철) · 7월계획",
            _owner(PERSON1_NAME),
        ]
    )
    for date, category, amt, memo, who in JULY_ACTUAL_EXPENSES:
        rows.append([date, category, amt, memo, _owner(who)])
    return rows


def build_income_rows() -> list[list]:
    from config.life_plan import JULY_ACTUAL_INCOME, JULY_NET_INCOME

    rows: list[list] = [
        ["날짜", "담당자", "유형", "금액", "메모"],
        [
            "2026-07-01",
            SHEET_P1,
            "급여",
            JULY_NET_INCOME,
            "7월 입금(6월 근무분·수습)",
        ],
    ]
    for date, kind, amt, memo, who in JULY_ACTUAL_INCOME:
        rows.append([date, _owner(who), kind, amt, memo])
    return rows


def build_asset_rows() -> list[list]:
    from config.life_plan import INVESTMENT_PRODUCTS

    rows: list[list] = [
        ["계좌유형", "계좌명", "담당자", "티커", "종목명", "수량", "평단가", "현재가"]
    ]
    for a in INVESTMENT_PRODUCTS:
        price = a["price"]
        rows.append(
            [
                a["account_type"],
                a["account_name"],
                _owner(a["owner"]),
                a.get("ticker", ""),
                a["name"],
                a.get("qty", 1),
                price,
                price,
            ]
        )
    return rows


def build_liability_rows() -> list[list]:
    from config.life_plan import LIABILITIES

    rows: list[list] = [
        ["부채유형", "부채명", "원금", "현재잔액", "연이자율(%)", "월상환액", "만기일", "연결자산"]
    ]
    for L in LIABILITIES:
        rows.append(
            [
                L["type"],
                L["name"],
                L["principal"],
                L["balance"],
                L["rate"],
                L["monthly"],
                L.get("maturity", ""),
                "",
            ]
        )
    return rows


def build_settings_rows(docs_id: str, drive_id: str) -> list[list]:
    from deploy.sheets_builder import ACCOUNT_TYPES, EXPENSE_CATEGORIES, INCOME_TYPES
    from config.life_plan import GOAL_DATE, GOAL_NET_WORTH

    budgets = july_budget()
    rows: list[list] = [
        ["항목", "값", "설명"],
        ["Person1 이름", SHEET_P1, "수입·지출 담당자1"],
        ["Person2 이름", SHEET_P2, "수입·지출 담당자2"],
        ["목표 순자산", GOAL_NET_WORTH, "원 단위"],
        ["목표 날짜", GOAL_DATE, "운정 59형 입주"],
        ["추세 계산 개월수", 6, "목표 예측용"],
        ["Docs 템플릿 ID", docs_id, "자동 생성됨"],
        ["Drive 폴더 ID", drive_id, "리포트 저장 폴더 (선택)"],
        ["", "", ""],
        ["계좌유형 목록", ", ".join(ACCOUNT_TYPES), ""],
        ["지출 카테고리", ", ".join(EXPENSE_CATEGORIES), ""],
        ["수입 유형", ", ".join(INCOME_TYPES), ""],
        ["", "", ""],
        ["자산 배분 목표(%)", "", "설정!B열에 목표 % 입력"],
    ]
    for acc in ACCOUNT_TYPES:
        rows.append([acc, 0, "목표 비중 %"])
    rows.append(["", "", ""])
    rows.append(["예산 (월 한도)", "", "7월·고정비 기준"])
    for cat in EXPENSE_CATEGORIES:
        rows.append([cat, budgets.get(cat, 0), "원/월"])
    return rows


def build_tax_rows() -> list[list]:
    from deploy.sheets_extended import TAX_LIMITS

    rows: list[list] = [["계좌", "연간한도", "올해납입", "잔여", "사용률", "상태", "메모"]]
    for i, (name, limit, note) in enumerate(TAX_LIMITS, start=2):
        rows.append(
            [
                name,
                limit,
                0,
                f"=MAX(0,B{i}-C{i})",
                f'=IF(B{i}=0,"",C{i}/B{i})',
                f'=IF(E{i}>=1,"초과",IF(E{i}>=0.8,"임박","여유"))',
                note,
            ]
        )
    return rows


def build_maturity_rows() -> list[list]:
    from config.life_plan import LIABILITIES

    rows: list[list] = [
        ["계좌유형", "계좌명", "상품명", "만기일", "D-day", "예상금액", "알림", "메모"]
    ]
    rows.append(
        [
            "ISA",
            f"{SHEET_P1}-ISA서민형",
            "ISA 3년",
            "2029-06-30",
            "=IF(D2=\"\",\"\",D2-TODAY())",
            0,
            '=IF(E2="","",IF(E2<=30,"임박","OK"))',
            "계약금",
        ]
    )
    r = 3
    for L in LIABILITIES:
        mat = L.get("maturity") or ""
        if not mat:
            continue
        rows.append(
            [
                L["type"],
                L["name"],
                L["name"],
                mat,
                f'=IF(D{r}="","",D{r}-TODAY())',
                L["balance"],
                f'=IF(E{r}="","",IF(E{r}<=30,"임박","OK"))',
                L.get("memo", ""),
            ]
        )
        r += 1
    return rows


def build_transfer_templates() -> list[list]:
    from config.life_plan import (
        FIXED_P1_JULY_ON_KB,
        JULY_TO_ALLOWANCE_P1,
        JULY_TO_CHEONGYAK,
        JULY_TO_FOOD,
        JULY_TO_JOINT,
        JULY_TO_SAMSUNG,
        P1_KB_BALANCE,
    )

    return [
        ["템플릿명", "이동유형", "출발_유형", "출발_명", "도착_유형", "도착_명", "메모"],
        [
            "7월→KB공동(월세·관리)",
            "계좌간이동",
            "현금",
            "문현철-KB고정비",
            "현금",
            "가계-KB공동",
            f"{JULY_TO_JOINT:,} · 월세·관리·전기 전액(평소 ½)",
        ],
        [
            "7월→카카오페이(식비)",
            "계좌간이동",
            "현금",
            "문현철-KB고정비",
            "현금",
            "문현철-카카오페이식비",
            f"{JULY_TO_FOOD:,} · 식비 공동",
        ],
        [
            "7월→하나청약",
            "계좌간이동",
            "현금",
            "문현철-KB고정비",
            "주택청약",
            "문현철-하나청약",
            f"{JULY_TO_CHEONGYAK:,}",
        ],
        [
            "7월→삼성증권(저축)",
            "계좌간이동",
            "현금",
            "문현철-KB고정비",
            "CMA",
            "문현철-삼성저축",
            f"{JULY_TO_SAMSUNG:,}",
        ],
        [
            "7월→토스용돈(금액보류)",
            "계좌간이동",
            "현금",
            "문현철-KB고정비",
            "현금",
            "문현철-토스용돈",
            f"{JULY_TO_ALLOWANCE_P1:,} · 통장만 등록·이체 안 함",
        ],
        [
            "▶ KB문현철 출발",
            "",
            "",
            "",
            "",
            "",
            f"잔액 {P1_KB_BALANCE:,} → 남김(고정비결제) {FIXED_P1_JULY_ON_KB:,}",
        ],
    ]


def build_scenario_rows() -> list[list]:
    from config.life_plan import JULY_BUFFER, MONTHLY_INVEST_TOTAL

    # A=7월 생존(버퍼만), B=10월~ 정상 저축
    rows: list[list] = [
        ["시나리오 비교 (순자산 예측)", "", "", ""],
        ["항목", "A: 7월 생존", "B: 정상저축(10월~)", "차이(B-A)"],
        ["월 저축액", JULY_BUFFER, MONTHLY_INVEST_TOTAL, "=C3-B3"],
        ["연 수익률", 0.03, 0.03, "=C4-B4"],
        ["일회성 지출", 0, 0, "=C5-B5"],
        ["지출 시점(개월)", 0, 0, "=C6-B6"],
        ["예측 기간(개월)", 60, 60, ""],
        ["", "", "", ""],
        ["월", "순자산 A", "순자산 B", "차이"],
    ]
    for m in range(0, 61):
        r = 10 + m
        if m == 0:
            fa = "='대시보드'!B5"
            fb = "='대시보드'!B5"
        else:
            prev = r - 1
            fa = f"=MAX(0,B{prev}*(1+$B$4/12)+$B$3-IF($B$6={m},$B$5,0))"
            fb = f"=MAX(0,C{prev}*(1+$C$4/12)+$C$3-IF($C$6={m},$C$5,0))"
        rows.append([m, fa, fb, f"=C{r}-B{r}"])
    return rows


def build_dsr_rows() -> list[list]:
    from config.life_plan import JULY_NET_INCOME

    rows: list[list] = [
        ["DSR · 상환 부담 분석", "", ""],
        ["연간 세전소득 (참고)", JULY_NET_INCOME * 12, "7월 세후×12 (수습 기준 참고)"],
        ["연간 원리금 상환", "=SUM('부채'!F:F)*12", "월상환×12"],
        ["DSR (%)", '=IF(B2=0,"",B3/B2)', "40% 이하 권장"],
        ["DSR 상태", '=IF(B4="","",IF(B4>0.4,"주의",IF(B4>0.3,"보통","양호")))', ""],
        ["월 가용여력", "=B2/12-SUM('부채'!F:F)-월간집계!B11", "소득-대출-지출"],
        ["", "", ""],
        ["부채별 상환 요약", "잔액", "월상환", "연상환", "만기"],
    ]
    for br in range(2, 12):
        out_r = br + 7
        rows.append(
            [
                f"=IF('부채'!B{br}=\"\",\"\",'부채'!B{br})",
                f"=IF('부채'!D{br}=\"\",\"\",'부채'!D{br})",
                f"=IF('부채'!F{br}=\"\",\"\",'부채'!F{br})",
                f"=IF(C{out_r}=\"\",\"\",C{out_r}*12)",
                f"=IF('부채'!G{br}=\"\",\"\",'부채'!G{br})",
            ]
        )
    return rows


def fix_daily_header() -> list[list]:
    return [
        ["📈 자산 일별 이력 — 담당자별·2인 합계"],
        ["매일 09:00 시세 갱신 후 자동 기록 · 오늘 날짜는 최신값으로 덮어씀"],
        ["날짜", '=설정!B2&" 자산"', '=설정!B3&" 자산"', "공동", "합계(2인+공동)"],
        [
            "2026-07-01",
            "=SUMIF('자산_종목'!C:C,설정!B2,'자산_종목'!I:I)",
            "=SUMIF('자산_종목'!C:C,설정!B3,'자산_종목'!I:I)",
            '=SUMIF(\'자산_종목\'!C:C,"공동",\'자산_종목\'!I:I)',
            "=B4+C4+D4",
        ],
    ]


def build_networth_history() -> list[list]:
    return [
        ["날짜", "총자산", "총부채", "순자산", "메모"],
        [
            "2026-07-01",
            "=월간집계!B5",
            "=월간집계!B6",
            "=월간집계!B7",
            "7월 고정비·KB잔액 반영",
        ],
    ]


def build_overview_rows() -> list[list]:
    """한눈에보기 — 수식은 life_phase / 월간집계 연동."""
    # 요약 블록(C11~)을 피하려고 페이즈 날짜 구간만 MATCH
    m = "MATCH(TODAY(),'라이프페이즈'!C$2:C$8,1)"
    phase_id = f"INDEX('라이프페이즈'!A$2:A$8,{m})"
    phase_name = f"INDEX('라이프페이즈'!B$2:B$8,{m})"
    belt = f"=INDEX('라이프페이즈'!E$2:E$8,{m})"
    target_free = f"=INDEX('라이프페이즈'!F$2:F$8,{m})"
    tasks = f"=INDEX('라이프페이즈'!G$2:G$8,{m})"
    return [
        ["✦ 재무관리 한눈에 보기", "", ""],
        ['=HYPERLINK("#gid=2","자산")', '=HYPERLINK("#gid=3","지출")', '=HYPERLINK("#gid=4","수입")'],
        ['=HYPERLINK("#gid=9","부채")', '=HYPERLINK("#gid=18","일별추이")', '=HYPERLINK("#gid=0","상세KPI")'],
        ['=HYPERLINK("#gid=11","세금")', '=HYPERLINK("#gid=13","DSR")', '=HYPERLINK("#gid=14","시나리오")'],
        ['=HYPERLINK("#gid=19","인생라인")', '=HYPERLINK("#gid=20","라이프페이즈")', '=HYPERLINK("#gid=21","분기체크")'],
        ["💡 7월: 고정비 계획 반영 · 여친 소득 0 · 건보 제외", "", ""],
        ["🎯 인생 단계 (오늘 기준)", "값", "메모"],
        ["현재 페이즈", f'={phase_id}&" "&{phase_name}', belt],
        ["이번 달 할 일", tasks, ""],
        # P0(7월) 목표 순저축 = 라이프페이즈 F열(JULY_BUFFER)
        ["목표 순저축", target_free, '=IF(B10="","",IF(B15>=B10,"달성","부족"))'],
        ["페이즈 목표 여유", target_free, ""],
        ["", "", ""],
        ["핵심 지표", "값", "상태"],
        ["순자산", "='대시보드'!B5", ""],
        ["순저축 (이번 달)", "=월간집계!B12", '=IF(월간집계!B13="","",TEXT(월간집계!B13,"0%"))'],
        ["DSR", "='DSR_상환'!B4", "='DSR_상환'!B5"],
        ["목표 진행률", "='대시보드'!B18", ""],
        ["비상자금", "=월간집계!B14", "개월"],
        ["", "", ""],
        ["7월 고정비 요약", "금액", ""],
        [
            "고정비 합(건보 제외)",
            (
                "=SUMIFS('지출'!C:C,'지출'!B:B,\"고정비\",'지출'!A:A,\">=2026-07-01\",'지출'!A:A,\"<=2026-07-31\")"
                "+SUMIFS('지출'!C:C,'지출'!B:B,\"교통\",'지출'!A:A,\">=2026-07-01\",'지출'!A:A,\"<=2026-07-31\")"
                "+SUMIFS('지출'!C:C,'지출'!B:B,\"대출상환\",'지출'!A:A,\">=2026-07-01\",'지출'!A:A,\"<=2026-07-31\")"
                "+SUMIFS('지출'!C:C,'지출'!B:B,\"대출이자\",'지출'!A:A,\">=2026-07-01\",'지출'!A:A,\"<=2026-07-31\")"
            ),
            "",
        ],
        ["KB 주거래", "=SUMIF('자산_종목'!E:E,\"KB 주거래\",'자산_종목'!I:I)", ""],
        ["총 지출(7월)", "=월간집계!B11", ""],
        ["총 수입(7월)", "=월간집계!B10", ""],
    ]


def update_values(sheets, sid: str, range_a1: str, rows: list[list]) -> None:
    sheets.spreadsheets().values().update(
        spreadsheetId=sid,
        range=range_a1,
        valueInputOption="USER_ENTERED",
        body={"values": rows},
    ).execute()


def clear_range(sheets, sid: str, range_a1: str) -> None:
    sheets.spreadsheets().values().clear(
        spreadsheetId=sid, range=range_a1
    ).execute()


def sync(spreadsheet_id: str) -> str:
    from deploy.auth import build_services, get_credentials

    sys.path.insert(0, str(ROOT / "scripts"))
    from sync_life_sheets import sync as sync_life  # noqa: E402

    creds = get_credentials(CONFIG_DIR)
    sheets, *_ = build_services(creds)

    # 기존 Docs/Drive ID 유지
    settings = (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range="'설정'!B7:B8")
        .execute()
        .get("values", [])
    )
    docs_id = settings[0][0] if settings and settings[0] else ""
    drive_id = settings[1][0] if len(settings) > 1 and settings[1] else ""

    # 데이터 탭 초기화 후 기록
    for rng in (
        "'지출'!A2:E500",
        "'수입'!A2:E100",
        "'자산_종목'!A2:H50",
        "'부채'!A2:H20",
        "'설정'!A1:C50",
        "'세금한도'!A1:G20",
        "'만기_캘린더'!A1:H20",
        "'이동_템플릿'!A1:G20",
        "'시나리오'!A1:D80",
        "'DSR_상환'!A1:E30",
        "'한눈에보기'!A1:C40",
        "'자산_일별이력'!A1:E10",
        "'순자산_이력'!A1:E10",
    ):
        clear_range(sheets, spreadsheet_id, rng)

    update_values(sheets, spreadsheet_id, "'설정'!A1", build_settings_rows(docs_id, drive_id))
    update_values(sheets, spreadsheet_id, "'지출'!A1", build_expense_rows())
    update_values(sheets, spreadsheet_id, "'수입'!A1", build_income_rows())
    update_values(sheets, spreadsheet_id, "'자산_종목'!A1", build_asset_rows())
    update_values(sheets, spreadsheet_id, "'부채'!A1", build_liability_rows())
    update_values(sheets, spreadsheet_id, "'세금한도'!A1", build_tax_rows())
    update_values(sheets, spreadsheet_id, "'만기_캘린더'!A1", build_maturity_rows())
    update_values(sheets, spreadsheet_id, "'이동_템플릿'!A1", build_transfer_templates())
    update_values(sheets, spreadsheet_id, "'시나리오'!A1", build_scenario_rows())
    update_values(sheets, spreadsheet_id, "'DSR_상환'!A1", build_dsr_rows())
    update_values(sheets, spreadsheet_id, "'한눈에보기'!A1", build_overview_rows())
    update_values(sheets, spreadsheet_id, "'자산_일별이력'!A1", fix_daily_header())
    update_values(sheets, spreadsheet_id, "'순자산_이력'!A1", build_networth_history())
    update_values(sheets, spreadsheet_id, "'월간집계'!B2:B3", [[2026], [7]])

    # 인생라인 3탭
    life_url = sync_life(spreadsheet_id)
    return life_url


def main() -> None:
    sheet_id = DEFAULT_SHEET_ID
    for arg in sys.argv[1:]:
        if arg.startswith("--id="):
            sheet_id = arg.split("=", 1)[1]

    if not (CONFIG_DIR / "credentials.json").exists():
        print("config/credentials.json 필요")
        sys.exit(1)

    from config.life_plan import FIXED_JULY_TOTAL, JULY_BUFFER, JULY_NET_INCOME

    budgets = july_budget()
    budget_sum = sum(budgets.values())
    url = sync(sheet_id)
    print("전 탭 동기화 완료")
    print(f"  7월 고정비(건보 제외): {FIXED_JULY_TOTAL:,}")
    print(f"  7월 예산 합(식비·용돈 포함): {budget_sum:,}")
    print(f"  7월 급여(세후): {JULY_NET_INCOME:,}")
    print(f"  7월 버퍼(목표 순저축): {JULY_BUFFER:,}")
    print(url)


if __name__ == "__main__":
    main()
