#!/usr/bin/env python3
"""Google 가게부 자산_종목·계좌목록에서 현재 계좌별 잔액 조회."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CONFIG_DIR = ROOT / "config"
DEFAULT_SPREADSHEET_ID = "1YAoC4VQHGLZpRBf267JW5uhMSrs2d5aHBUvNJuNBoRk"


def _parse_krw(raw: object) -> int:
    if raw is None or raw == "":
        return 0
    s = str(raw).strip().replace(",", "")
    if not s:
        return 0
    try:
        return int(float(s))
    except ValueError:
        return 0


def _fetch_range(sheets, spreadsheet_id: str, range_a1: str) -> list[list]:
    result = (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_a1, valueRenderOption="UNFORMATTED_VALUE")
        .execute()
    )
    return result.get("values", [])


def fetch_asset_positions(spreadsheet_id: str) -> list[dict[str, str | int]]:
    from deploy.auth import build_services, get_credentials

    creds = get_credentials(CONFIG_DIR)
    sheets, _, _, _ = build_services(creds)
    rows = _fetch_range(sheets, spreadsheet_id, "자산_종목!A2:N500")

    out: list[dict[str, str | int]] = []
    for raw in rows:
        if len(raw) < 2:
            continue
        acct_type = str(raw[0]).strip() if raw[0] else ""
        acct_name = str(raw[1]).strip() if len(raw) > 1 and raw[1] else ""
        owner = str(raw[2]).strip() if len(raw) > 2 and raw[2] else ""
        product = str(raw[4]).strip() if len(raw) > 4 and raw[4] else ""
        if not acct_name and not product:
            continue

        val = 0
        if len(raw) > 8 and raw[8] not in (None, ""):
            val = _parse_krw(raw[8])
        elif len(raw) > 7 and raw[7] not in (None, ""):
            qty = float(raw[5]) if len(raw) > 5 and raw[5] not in (None, "") else 1.0
            val = int(qty * _parse_krw(raw[7]))

        if val == 0 and not acct_type:
            continue

        out.append(
            {
                "type": acct_type,
                "account": acct_name or product,
                "owner": owner,
                "product": product,
                "value": val,
            }
        )
    return out


def fetch_account_list(spreadsheet_id: str) -> list[dict[str, str | int]]:
    from deploy.auth import build_services, get_credentials

    creds = get_credentials(CONFIG_DIR)
    sheets, _, _, _ = build_services(creds)
    rows = _fetch_range(sheets, spreadsheet_id, "계좌목록!A2:D200")

    out: list[dict[str, str | int]] = []
    for raw in rows:
        if len(raw) < 2:
            continue
        name = str(raw[0]).strip() if raw[0] else ""
        if not name or name.startswith("=") or "자동" in name or "통장" in name and "추가" in name:
            continue
        val = _parse_krw(raw[1]) if len(raw) > 1 else 0
        if val <= 0:
            continue
        owner = str(raw[2]).strip() if len(raw) > 2 and raw[2] else ""
        acct_type = str(raw[3]).strip() if len(raw) > 3 and raw[3] else ""
        out.append({"account": name, "value": val, "owner": owner, "type": acct_type})
    return out


def aggregate_by_account(positions: list[dict[str, str | int]]) -> list[dict[str, str | int]]:
    totals: dict[tuple[str, str], int] = defaultdict(int)
    types: dict[tuple[str, str], str] = {}
    for p in positions:
        key = (str(p["account"]), str(p["owner"]))
        totals[key] += int(p["value"])
        if p.get("type"):
            types[key] = str(p["type"])
    return [
        {"account": k[0], "owner": k[1], "type": types.get(k, ""), "value": v}
        for k, v in sorted(totals.items(), key=lambda x: -x[1])
        if v > 0
    ]


def aggregate_by_owner(positions: list[dict[str, str | int]]) -> dict[str, int]:
    totals: dict[str, int] = defaultdict(int)
    for p in positions:
        owner = str(p["owner"]) or "(미지정)"
        totals[owner] += int(p["value"])
    return dict(sorted(totals.items(), key=lambda x: -x[1]))


def print_report(positions: list[dict], account_list: list[dict] | None) -> None:
    by_acct = aggregate_by_account(positions)
    by_owner = aggregate_by_owner(positions)
    total = sum(int(p["value"]) for p in positions)

    print(f"\n{'=' * 72}")
    print("  Google 가게부 — 현재 계좌별 잔액 (자산_종목)")
    print(f"{'=' * 72}")
    print(f"\n총 자산: {total:,}원\n")

    print("[담당자별 합계]")
    for owner, val in by_owner.items():
        print(f"  {owner:<8} {val:>14,}원")

    print(f"\n[계좌별 합계] ({len(by_acct)}개)")
    print(f"{'담당자':<8} {'계좌명':<28} {'유형':<10} {'평가(원)':>14}")
    print("-" * 72)
    for row in by_acct:
        print(
            f"{row['owner']:<8} {row['account']:<28} {row['type']:<10} {int(row['value']):>14,}"
        )

    if positions:
        print(f"\n[종목·상세] ({len(positions)}행)")
        print(f"{'담당자':<8} {'계좌명':<24} {'종목':<16} {'평가(원)':>14}")
        print("-" * 72)
        for p in sorted(positions, key=lambda x: (-int(x["value"]), str(x["account"]))):
            if int(p["value"]) <= 0:
                continue
            print(
                f"{p['owner']:<8} {p['account']:<24} {str(p['product'])[:16]:<16} {int(p['value']):>14,}"
            )

    if account_list:
        print(f"\n[계좌목록 시트] ({len(account_list)}개)")
        for row in account_list:
            print(f"  {row['account']:<28} {int(row['value']):>14,}원")


def main() -> None:
    parser = argparse.ArgumentParser(description="Google 가게부 계좌별 잔액 조회")
    parser.add_argument("--id", default=DEFAULT_SPREADSHEET_ID, help="스프레드시트 ID")
    parser.add_argument("--accounts-only", action="store_true", help="계좌목록 시트만")
    args = parser.parse_args()

    try:
        if args.accounts_only:
            account_list = fetch_account_list(args.id)
            positions = []
        else:
            positions = fetch_asset_positions(args.id)
            account_list = None
            try:
                account_list = fetch_account_list(args.id)
            except Exception:
                account_list = None
        print_report(positions, account_list)
    except FileNotFoundError as e:
        print(e)
        print(
            "\n인증 방법:\n"
            "1. Google Cloud Console → OAuth 클라이언트(데스크톱) 생성\n"
            "2. JSON을 config/credentials.json 으로 저장\n"
            f"3. python scripts/fetch_google_balances.py --id {args.id}\n"
            "   (브라우저 로그인 후 config/token.json 자동 생성)"
        )
        sys.exit(1)
    except Exception as e:
        print(f"조회 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
