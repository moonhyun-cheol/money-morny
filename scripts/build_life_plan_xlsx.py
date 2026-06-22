#!/usr/bin/env python3
"""인생 플랜 Excel(xlsx) 생성."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.life_plan import (  # noqa: E402
    ALLOWANCE_P1,
    ALLOWANCE_P2,
    ANNUAL_INCOME_P1,
    ANNUAL_INCOME_P2,
    CONTRACT_DEPOSIT_TARGET,
    FIXED_MONTHLY_TOTAL,
    FOOD_GROCERY,
    HOUSING_GOAL,
    INVESTMENT_PRODUCTS,
    LIABILITIES,
    MARRIAGE_PLAN,
    MONTHLY_INVEST_TOTAL,
    NET_INCOME_HOUSEHOLD,
    PERSON1_NAME,
    PERSON2_NAME,
    PENSION_PLAN_P1,
    PENSION_TAX_CREDIT_RATE,
    SAVE_HOUSE,
    SAVE_ISA,
    SAVE_PENSION_P1,
    SAVE_VISA_BUFFER_P2,
    SAVE_YOUTH_LEAP,
)

try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
except ImportError:
    print("openpyxl 필요: pip install openpyxl")
    raise

OUT = ROOT / "sheets" / "인생플랜.xlsx"

HEADER_FILL = PatternFill("solid", fgColor="2C3E50")
HEADER_FONT = Font(color="FFFFFF", bold=True)
TITLE_FONT = Font(bold=True, size=14)


def _header_row(ws, row: int, values: list) -> None:
    for c, v in enumerate(values, 1):
        cell = ws.cell(row=row, column=c, value=v)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")


def sheet_overview(wb: Workbook) -> None:
    ws = wb.active
    ws.title = "개요"
    ws["A1"] = "인생 플랜 (운정 59형 · 2인 가구)"
    ws["A1"].font = TITLE_FONT
    rows = [
        ("작성일", date.today().isoformat()),
        ("Person1", f"{PERSON1_NAME} (연 {ANNUAL_INCOME_P1:,}만)"),
        ("Person2", f"{PERSON2_NAME} (연 {ANNUAL_INCOME_P2:,}만)"),
        ("혼인", MARRIAGE_PLAN),
        ("주택 목표", HOUSING_GOAL),
        ("월 세후 합산", NET_INCOME_HOUSEHOLD),
        ("월 고정비", FIXED_MONTHLY_TOTAL),
        ("월 식비(장보기)", FOOD_GROCERY),
        ("월 용돈", ALLOWANCE_P1 + ALLOWANCE_P2),
        ("월 투자·저축", MONTHLY_INVEST_TOTAL),
        ("계약금 목표", CONTRACT_DEPOSIT_TARGET),
    ]
    for i, (k, v) in enumerate(rows, 3):
        ws.cell(row=i, column=1, value=k)
        ws.cell(row=i, column=2, value=v)
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 48


def sheet_monthly_budget(wb: Workbook) -> None:
    ws = wb.create_sheet("월예산")
    _header_row(ws, 1, ["구분", "항목", "월(원)", "담당", "메모"])
    data = [
        ("고정비", "월세+관리비", 700_000, "공동", ""),
        ("고정비", "전기", 40_000, "공동", ""),
        ("고정비", "휴대폰", 60_000, "공동", ""),
        ("고정비", "교통(K-패스 실부담)", 100_000, "각자", "본인 9700×22, 여친 3800×17"),
        ("고정비", "보험", 250_000, "공동", ""),
        ("고정비", "구독·기타", 150_000, "공동", ""),
        ("고정비", "대출(300만 6.6%)", 92_000, PERSON1_NAME, "햇살론·장학금 제외"),
        ("식비", "주간 장보기", FOOD_GROCERY, "공동", "배달·외식 거의 없음"),
        ("용돈", "개인 용돈", ALLOWANCE_P1, PERSON1_NAME, "취미·의류 등"),
        ("용돈", "개인 용돈", ALLOWANCE_P2, PERSON2_NAME, ""),
        ("저축", "청년도약", SAVE_YOUTH_LEAP, PERSON1_NAME, "한도 70만"),
        ("저축", "ISA 서민형", SAVE_ISA, PERSON1_NAME, "예금·MMF"),
        ("저축", "집마련", SAVE_HOUSE, "공동", ""),
        ("저축", "연금저축", SAVE_PENSION_P1, PERSON1_NAME, "세액공제용"),
        ("저축", "비자 비상", SAVE_VISA_BUFFER_P2, PERSON2_NAME, "TOPIK6, 300만"),
        ("저축", "청약 추가납입", 0, PERSON1_NAME, "640만 유지"),
    ]
    for r, row in enumerate(data, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
    total_row = len(data) + 2
    ws.cell(row=total_row, column=2, value="합계")
    ws.cell(row=total_row, column=3, value=f"=SUM(C2:C{total_row - 1})")
    ws.cell(row=total_row + 1, column=2, value="세후 수입")
    ws.cell(row=total_row + 1, column=3, value=NET_INCOME_HOUSEHOLD)
    ws.cell(row=total_row + 2, column=2, value="잔액")
    ws.cell(row=total_row + 2, column=3, value=f"=C{total_row + 1}-C{total_row}")


def sheet_investments(wb: Workbook) -> None:
    ws = wb.create_sheet("투자종목")
    _header_row(ws, 1, ["계좌유형", "계좌명", "담당", "종목/상품", "월납입", "연한도", "목적", "비고"])
    products = [
        ("청년도약", "현철-청년도약", PERSON1_NAME, "정부기여+이자", SAVE_YOUTH_LEAP, 8_400_000, "2032 주택 해지", "본인만"),
        ("ISA", "현철-ISA", PERSON1_NAME, "MMF/예금", SAVE_ISA, 20_000_000, "2029 계약금", "서민형 3년"),
        ("주택청약", "현철-청약", PERSON1_NAME, "종합저축", 20_000, None, "청약 순위", "640만 유지"),
        ("연금저축", "현철-연금", PERSON1_NAME, "연금저축", SAVE_PENSION_P1, 6_000_000, "세액공제", "비혼 개인"),
        ("현금", "집마련", "공동", "집마련통장", SAVE_HOUSE, None, "잔금·부대비", ""),
        ("현금", "여친-비상", PERSON2_NAME, "비자·비상", SAVE_VISA_BUFFER_P2, None, "D-10/F-6", "TOPIK6"),
    ]
    for r, row in enumerate(products, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)


def sheet_tax(wb: Workbook) -> None:
    ws = wb.create_sheet("세금최적화")
    ws["A1"] = "비혼 기간 · 2인 각각 신고 (합산신고 불가)"
    ws["A1"].font = TITLE_FONT
    _header_row(ws, 3, ["항목", PERSON1_NAME, PERSON2_NAME, "메모"])
    credit = int(PENSION_PLAN_P1 * PENSION_TAX_CREDIT_RATE)
    rows = [
        ("연 소득(만)", ANNUAL_INCOME_P1, ANNUAL_INCOME_P2, "세전"),
        ("연금저축 납입(연)", PENSION_PLAN_P1, 0, "P1 300~400만 권장"),
        ("연금 세액공제(15%)", credit, 0, "P2 환급효과 미미"),
        ("ISA 납입", SAVE_ISA * 12, 0, "세액공제 없음·이자비과세"),
        ("청년도약", SAVE_YOUTH_LEAP * 12, 0, "외국인 P2 불가"),
        ("체크카드 소득공제", "생활비·장보기", "알바급여", "전통시장·가맹 30% 등"),
        ("신용카드", "고정비 일부", "-", "15% 구간"),
        ("예상 추가 환급(연)", f"{credit + 50_000:,}원", "~0~10만", "연말정산"),
        ("혼인 후", "-", "-", "신혼특공·디딤돌 8,500만 이하"),
    ]
    for r, row in enumerate(rows, 4):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)


def sheet_timeline(wb: Workbook) -> None:
    ws = wb.create_sheet("타임라인")
    _header_row(ws, 1, ["시기", "구분", "할 일", "목표 잔고(집자금)"])
    milestones = [
        ("2026.07", "저축", "고정비·장보기 루틴, 청년도약·ISA 개설", 0),
        ("2026.07", "비자", "여친 근무 시작, 구직활동 증빙", 0),
        ("2027.02", "비자", "D-10 연장 (TOPIK6)", 300_000),
        ("2027.12", "혼인", "혼인신고·F-6 (목표)", 40_000_000),
        ("2028.H2", "청약", "운정 59형 신혼특공", 50_000_000),
        ("2029", "분양", "계약금·중도금(집단대출)", 60_000_000),
        ("2031~32", "입주", "디딤돌 3.2억 + 현금 1억", 100_000_000),
    ]
    cum = 0
    monthly_save = SAVE_HOUSE + SAVE_ISA + SAVE_YOUTH_LEAP
    for r, (when, cat, task, _) in enumerate(milestones, 2):
        ws.cell(row=r, column=1, value=when)
        ws.cell(row=r, column=2, value=cat)
        ws.cell(row=r, column=3, value=task)
    # 월별 시뮬
    ws2 = wb.create_sheet("월별저축")
    _header_row(ws2, 1, ["월차", "년월", "월저축", "누적(집자금)"])
    start = date(2026, 7, 1)
    cum = 0
    for m in range(36):
        y = start.year + (start.month - 1 + m) // 12
        mo = (start.month - 1 + m) % 12 + 1
        add = monthly_save if m > 0 else 0
        if m == 0:
            add = 0
        cum += add
        ws2.cell(row=m + 2, column=1, value=m)
        ws2.cell(row=m + 2, column=2, value=f"{y}-{mo:02d}")
        ws2.cell(row=m + 2, column=3, value=add)
        ws2.cell(row=m + 2, column=4, value=cum)


def sheet_allowance(wb: Workbook) -> None:
    ws = wb.create_sheet("용돈")
    _header_row(ws, 1, ["담당", "월 용돈", "포함", "미포함"])
    ws.cell(row=2, column=1, value=PERSON1_NAME)
    ws.cell(row=2, column=2, value=ALLOWANCE_P1)
    ws.cell(row=2, column=3, value="개인 취미·의류·PC")
    ws.cell(row=2, column=4, value="장보기·고정비·저축")
    ws.cell(row=3, column=1, value=PERSON2_NAME)
    ws.cell(row=3, column=2, value=ALLOWANCE_P2)
    ws.cell(row=3, column=3, value="개인 소비")
    ws.cell(row=3, column=4, value="공동 식비")


def main() -> None:
    wb = Workbook()
    sheet_overview(wb)
    sheet_monthly_budget(wb)
    sheet_investments(wb)
    sheet_tax(wb)
    sheet_timeline(wb)
    sheet_allowance(wb)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(f"생성: {OUT}")


if __name__ == "__main__":
    main()
