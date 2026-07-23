#!/usr/bin/env python3
"""플랜·Google 가게부 기준 계좌별 상시 잔액 역산."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CONFIG_DIR = ROOT / "config"

# Google 자산_종목 계좌명 ↔ life_plan 금융사
SHEET_ACCOUNT_ALIASES: dict[str, str] = {
    f"{__import__('config.life_plan', fromlist=['PERSON1_NAME']).PERSON1_NAME}-청약통장": "청약",
}


def _sheet_name_for(institution: str, owner: str) -> str:
    from config.life_plan import PERSON1_NAME, PERSON2_NAME

    mapping = {
        ("KB 공동", "공동"): "공동-KB공동",
        ("KB 주거래", PERSON1_NAME): f"{PERSON1_NAME}-KB주거래",
        ("토스", PERSON1_NAME): f"{PERSON1_NAME}-토스용돈",
        ("토스", PERSON2_NAME): f"{PERSON2_NAME}-토스용돈",
        ("삼성증권", PERSON1_NAME): f"{PERSON1_NAME}-삼성CMA",
        ("기존 청약", PERSON1_NAME): f"{PERSON1_NAME}-청약통장",
        ("알바 급여 은행", PERSON2_NAME): f"{PERSON2_NAME}-알바은행",
        ("토스뱅크", PERSON2_NAME): f"{PERSON2_NAME}-비자비상",
    }
    return mapping.get((institution, owner), f"{owner}-{institution}")


def reverse_steady_balances(pay_year: int, pay_month: int) -> list[dict[str, str | int]]:
    """급여 입금월 기준 — 급여일 직후 각 통장에 남아야 할 상시 잔액."""
    from config.life_plan import (
        ALLOWANCE_P1,
        ALLOWANCE_P1_JULY,
        ALLOWANCE_P2,
        ALLOWANCE_P2_JULY,
        CHEONGYAK_BALANCE,
        COHAB_CONTRIBUTION_P2,
        COHAB_P1_TRANSFER,
        COHAB_P1_TRANSFER_JULY,
        FIXED_BUFFER_P1,
        FIXED_BUFFER_P2,
        FIXED_JULY_TOTAL,
        FOOD_GROCERY,
        FOOD_JULY,
        HOUSEHOLD_JOINT_BANK,
        HOUSEHOLD_JOINT_BUFFER,
        HOUSEHOLD_JOINT_BUFFER_JULY,
        JULY_BUFFER,
        NET_INCOME_P1,
        P1_ALLOWANCE_BANK,
        P1_SALARY_HUB,
        P1_SECURITIES,
        P1_SUBSCRIPTION_BANK,
        P2_ALLOWANCE_BANK,
        P2_SALARY_BANK,
        P2_TOSS_BANK,
        PERSON1_NAME,
        PERSON2_NAME,
        REAL_WALLETS,
        SAVE_HOUSE_P1,
        SAVE_HOUSE_P2,
        SAVE_ISA,
        SAVE_PENSION_P1,
        SAVE_P2_TOSS_MONTHLY,
        SAVE_VISA_BUFFER_P2,
        household_net_for_paycheck,
    )

    p1, p2, _ = household_net_for_paycheck(pay_year, pay_month)
    july = pay_year == 2026 and pay_month == 7

    if july:
        kb_after = p1 - FIXED_JULY_TOTAL - FOOD_JULY - ALLOWANCE_P1_JULY - ALLOWANCE_P2_JULY - JULY_BUFFER
        return [
            {
                "sheet_account": _sheet_name_for(P1_SALARY_HUB, PERSON1_NAME),
                "wallet": P1_SALARY_HUB,
                "owner": PERSON1_NAME,
                "steady": max(kb_after, 0),
                "inflow": p1,
                "outflow": p1 - max(kb_after, 0) - JULY_BUFFER,
                "memo": "7월 생존·이체 후 KB 잔액 0 (고정·식비·용돈 직접 결제)",
            },
            {
                "sheet_account": _sheet_name_for(HOUSEHOLD_JOINT_BANK, "공동"),
                "wallet": HOUSEHOLD_JOINT_BANK,
                "owner": "공동",
                "steady": 0,
                "inflow": 0,
                "outflow": 0,
                "memo": "7월은 KB주거래에서 월세·식비 직접 결제 (공동 미운용)",
            },
            {
                "sheet_account": _sheet_name_for(P1_SECURITIES, PERSON1_NAME),
                "wallet": f"{P1_SECURITIES} CMA",
                "owner": PERSON1_NAME,
                "steady": JULY_BUFFER,
                "inflow": JULY_BUFFER,
                "outflow": 0,
                "memo": "7월 생존 잔액·ISA/연금 보류",
            },
            {
                "sheet_account": _sheet_name_for(P1_SUBSCRIPTION_BANK, PERSON1_NAME),
                "wallet": P1_SUBSCRIPTION_BANK,
                "owner": PERSON1_NAME,
                "steady": CHEONGYAK_BALANCE,
                "inflow": 0,
                "outflow": 0,
                "memo": "청약 잔액 유지",
            },
        ]

    rows: list[dict[str, str | int]] = [
        {
            "sheet_account": _sheet_name_for(HOUSEHOLD_JOINT_BANK, "공동"),
            "wallet": HOUSEHOLD_JOINT_BANK,
            "owner": "공동",
            "steady": HOUSEHOLD_JOINT_BUFFER,
            "inflow": COHAB_P1_TRANSFER + (COHAB_CONTRIBUTION_P2 if p2 else 0),
            "outflow": HOUSEHOLD_JOINT_BUFFER,
            "memo": "월세·전기·장보기 결제 버퍼",
        },
        {
            "sheet_account": _sheet_name_for(P1_SALARY_HUB, PERSON1_NAME),
            "wallet": P1_SALARY_HUB,
            "owner": PERSON1_NAME,
            "steady": FIXED_BUFFER_P1,
            "inflow": p1,
            "outflow": p1 - FIXED_BUFFER_P1,
            "memo": "급여→이체·개인고정 결제 후 버퍼",
        },
        {
            "sheet_account": _sheet_name_for(P1_ALLOWANCE_BANK, PERSON1_NAME),
            "wallet": P1_ALLOWANCE_BANK,
            "owner": PERSON1_NAME,
            "steady": ALLOWANCE_P1,
            "inflow": ALLOWANCE_P1,
            "outflow": ALLOWANCE_P1,
            "memo": "용돈 전용",
        },
        {
            "sheet_account": _sheet_name_for(P1_SECURITIES, PERSON1_NAME),
            "wallet": f"{P1_SECURITIES} CMA",
            "owner": PERSON1_NAME,
            "steady": SAVE_HOUSE_P1,
            "inflow": SAVE_HOUSE_P1,
            "outflow": 0,
            "memo": "월 입금·누적 (별도)",
        },
        {
            "sheet_account": f"{PERSON1_NAME}-ISA서민형",
            "wallet": f"{P1_SECURITIES} ISA",
            "owner": PERSON1_NAME,
            "steady": SAVE_ISA,
            "inflow": SAVE_ISA,
            "outflow": 0,
            "memo": "월 입금·누적 (별도)",
        },
        {
            "sheet_account": f"{PERSON1_NAME}-연금저축",
            "wallet": f"{P1_SECURITIES} 연금",
            "owner": PERSON1_NAME,
            "steady": SAVE_PENSION_P1,
            "inflow": SAVE_PENSION_P1,
            "outflow": 0,
            "memo": "월 입금·누적 (별도)",
        },
        {
            "sheet_account": _sheet_name_for(P1_SUBSCRIPTION_BANK, PERSON1_NAME),
            "wallet": P1_SUBSCRIPTION_BANK,
            "owner": PERSON1_NAME,
            "steady": CHEONGYAK_BALANCE,
            "inflow": 20_000,
            "outflow": 0,
            "memo": "잔액 640만 유지",
        },
    ]

    if p2 > 0:
        rows.extend(
            [
                {
                    "sheet_account": _sheet_name_for(P2_SALARY_BANK, PERSON2_NAME),
                    "wallet": P2_SALARY_BANK,
                    "owner": PERSON2_NAME,
                    "steady": FIXED_BUFFER_P2,
                    "inflow": p2,
                    "outflow": p2 - FIXED_BUFFER_P2,
                    "memo": "급여→이체·본인고정 후 버퍼",
                },
                {
                    "sheet_account": _sheet_name_for(P2_ALLOWANCE_BANK, PERSON2_NAME),
                    "wallet": P2_ALLOWANCE_BANK,
                    "owner": PERSON2_NAME,
                    "steady": ALLOWANCE_P2,
                    "inflow": ALLOWANCE_P2,
                    "outflow": ALLOWANCE_P2,
                    "memo": "용돈 전용",
                },
                {
                    "sheet_account": f"{PERSON2_NAME}-비자비상",
                    "wallet": P2_TOSS_BANK,
                    "owner": PERSON2_NAME,
                    "steady": SAVE_P2_TOSS_MONTHLY,
                    "inflow": SAVE_P2_TOSS_MONTHLY,
                    "outflow": 0,
                    "memo": f"집마련 {SAVE_HOUSE_P2:,} + 비자 {SAVE_VISA_BUFFER_P2:,} (비자 몫 유지)",
                },
            ]
        )

    return rows


def cumulative_balances_through(pay_year: int, pay_month: int) -> dict[str, int]:
    """급여 스케줄 누적 — 저축 계좌 예상 잔액 (이자 제외)."""
    from config.life_plan import (
        CHEONGYAK_BALANCE,
        PAYROLL_SCHEDULE_2026,
        SAVE_HOUSE_P1,
        SAVE_HOUSE_P2,
        SAVE_ISA,
        SAVE_PENSION_P1,
        SAVE_VISA_BUFFER_P2,
    )

    cum = {
        f"CMA": 0,
        f"ISA": 0,
        f"연금": 0,
        f"토스뱅 파킹": 0,
        f"청약": CHEONGYAK_BALANCE,
    }

    for row in PAYROLL_SCHEDULE_2026:
        if row["pay_year"] > pay_year or (
            row["pay_year"] == pay_year and row["pay_month"] > pay_month
        ):
            break
        if row.get("july_survival"):
            cum["CMA"] += int(row["save_total"])
            continue
        cum["CMA"] += int(row.get("save_house_p1", 0))
        cum["ISA"] += int(row.get("save_isa", 0))
        cum["연금"] += int(row.get("save_pension", 0))
        house_p2 = int(row.get("save_house_p2", 0))
        visa = int(row.get("save_visa", 0))
        cum["토스뱅 파킹"] += house_p2 + visa
        if row["pay_month"] >= 10:
            cum["청약"] += 20_000

    return cum


def fetch_google_assets(spreadsheet_id: str) -> list[dict[str, str | int | float]]:
    from deploy.auth import build_services, get_credentials

    creds = get_credentials(CONFIG_DIR)
    sheets, _, _, _ = build_services(creds)
    result = sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="자산_종목!A2:I500",
    ).execute()
    rows: list[dict[str, str | int | float]] = []
    for raw in result.get("values", []):
        if len(raw) < 2:
            continue
        acct_type = str(raw[0]).strip() if raw[0] else ""
        acct_name = str(raw[1]).strip() if len(raw) > 1 and raw[1] else ""
        owner = str(raw[2]).strip() if len(raw) > 2 and raw[2] else ""
        val = 0
        if len(raw) > 8 and raw[8]:
            try:
                val = int(float(str(raw[8]).replace(",", "")))
            except ValueError:
                val = 0
        elif len(raw) > 7 and raw[7]:
            try:
                qty = float(raw[5]) if len(raw) > 5 and raw[5] else 1
                price = float(str(raw[7]).replace(",", ""))
                val = int(qty * price)
            except ValueError:
                val = 0
        if acct_name and val > 0:
            rows.append(
                {
                    "account_type": acct_type,
                    "account_name": acct_name,
                    "owner": owner,
                    "value": val,
                }
            )
    return rows


def print_report(pay_year: int, pay_month: int, google_rows: list | None = None) -> None:
    steady = reverse_steady_balances(pay_year, pay_month)
    cum = cumulative_balances_through(pay_year, pay_month)

    print(f"\n{'=' * 72}")
    print(f"  계좌별 잔액 역산 - {pay_year}-{pay_month:02d} 급여 입금월 기준")
    print(f"{'=' * 72}")

    print("\n[1] 급여일 직후 상시 잔액 (역산)")
    print(f"{'Google계좌명':<28} {'실제통장':<16} {'상시잔액':>12} {'월유입':>10} {'메모'}")
    print("-" * 72)
    for r in steady:
        print(
            f"{r['sheet_account']:<28} {r['wallet']:<16} "
            f"{int(r['steady']):>12,} {int(r['inflow']):>10,}  {r['memo']}"
        )

    print(f"\n[2] 저축 계좌 누적 (이자 제외·{pay_year}-{pay_month:02d}까지)")
    for name, val in cum.items():
        print(f"  {name:<12} {val:>12,}원")

    if google_rows is not None:
        print("\n[3] Google 자산_종목 실제 vs 플랜")
        actual_by_name = {r["account_name"]: r["value"] for r in google_rows}
        print(f"{'Google계좌명':<28} {'실제(시트)':>14} {'플랜상시':>12} {'차이':>12}")
        print("-" * 72)
        for r in steady:
            name = str(r["sheet_account"])
            plan = int(r["steady"])
            actual = int(actual_by_name.get(name, 0))
            if actual or plan:
                print(f"{name:<28} {actual:>14,} {plan:>12,} {actual - plan:>+12,}")
        for name, val in actual_by_name.items():
            if not any(str(s["sheet_account"]) == name for s in steady):
                print(f"{name:<28} {int(val):>14,} {'-':>12} {'-':>12}")


def main() -> None:
    parser = argparse.ArgumentParser(description="계좌별 잔액 역산")
    parser.add_argument("--year", type=int, default=date.today().year)
    parser.add_argument("--month", type=int, default=date.today().month)
    parser.add_argument("--id", dest="spreadsheet_id", default="", help="Google 스프레드시트 ID")
    args = parser.parse_args()

    google_rows = None
    if args.spreadsheet_id:
        try:
            google_rows = fetch_google_assets(args.spreadsheet_id)
        except FileNotFoundError as e:
            print(e)
            print("-> config/credentials.json 없으면 플랜 역산만 출력합니다.")
        except Exception as e:
            print(f"Google 읽기 실패: {e}")

    print_report(args.year, args.month, google_rows)


if __name__ == "__main__":
    main()
