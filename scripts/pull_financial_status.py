#!/usr/bin/env python3
"""Google 가게부에서 최신 재무상태 일괄 pull (자산·부채·KPI)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
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


def _fetch(sheets, sid: str, range_a1: str) -> list[list]:
    return (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=sid, range=range_a1, valueRenderOption="UNFORMATTED_VALUE")
        .execute()
        .get("values", [])
    )


def _fetch_formatted(sheets, sid: str, range_a1: str) -> list[list]:
    return (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=sid, range=range_a1, valueRenderOption="FORMATTED_VALUE")
        .execute()
        .get("values", [])
    )


def pull(spreadsheet_id: str) -> dict:
    from deploy.auth import build_services, get_credentials

    creds = get_credentials(CONFIG_DIR)
    sheets, _, _, _ = build_services(creds)

    meta = sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    title = meta.get("properties", {}).get("title", "")

    # ── 자산_종목 ──
    assets_raw = _fetch(sheets, spreadsheet_id, "자산_종목!A2:N500")
    positions: list[dict] = []
    for raw in assets_raw:
        if len(raw) < 2:
            continue
        acct_type = str(raw[0]).strip() if raw[0] else ""
        acct_name = str(raw[1]).strip() if len(raw) > 1 and raw[1] else ""
        owner = str(raw[2]).strip() if len(raw) > 2 and raw[2] else ""
        product = str(raw[4]).strip() if len(raw) > 4 and raw[4] else ""
        if not acct_name and not product:
            continue
        val = _parse_krw(raw[8]) if len(raw) > 8 else 0
        if val == 0 and len(raw) > 7 and raw[7]:
            qty = float(raw[5]) if len(raw) > 5 and raw[5] not in (None, "") else 1.0
            val = int(qty * _parse_krw(raw[7]))
        if val == 0 and not acct_type:
            continue
        positions.append(
            {"type": acct_type, "account": acct_name or product, "owner": owner, "product": product, "value": val}
        )

    by_account: dict[tuple[str, str], dict] = {}
    for p in positions:
        key = (p["account"], p["owner"])
        if key not in by_account:
            by_account[key] = {"type": p["type"], "value": 0}
        by_account[key]["value"] += int(p["value"])
        if p["type"]:
            by_account[key]["type"] = p["type"]

    by_owner: dict[str, int] = defaultdict(int)
    for p in positions:
        by_owner[p["owner"] or "(미지정)"] += int(p["value"])

    # ── 부채 ──
    debt_raw = _fetch(sheets, spreadsheet_id, "부채!A2:I200")
    debts: list[dict] = []
    for raw in debt_raw:
        if len(raw) < 4:
            continue
        name = str(raw[1]).strip() if len(raw) > 1 and raw[1] else ""
        balance = _parse_krw(raw[3]) if len(raw) > 3 else 0
        if not name or balance <= 0:
            continue
        debts.append({"type": str(raw[0]).strip() if raw[0] else "", "name": name, "balance": balance})

    # ── KPI (월간집계·대시보드) ──
    monthly = _fetch_formatted(sheets, spreadsheet_id, "월간집계!A1:B20")
    dashboard = _fetch_formatted(sheets, spreadsheet_id, "대시보드!A1:B25")

    def _kv(rows: list[list]) -> dict[str, str]:
        out: dict[str, str] = {}
        for row in rows:
            if len(row) >= 2 and row[0]:
                out[str(row[0]).strip()] = str(row[1]).strip() if row[1] is not None else ""
        return out

    monthly_kv = _kv(monthly)
    dash_kv = _kv(dashboard)

    total_assets = sum(int(p["value"]) for p in positions)
    total_debt = sum(d["balance"] for d in debts)
    net_worth = total_assets - total_debt

    return {
        "pulled_at": datetime.now().isoformat(timespec="seconds"),
        "spreadsheet_id": spreadsheet_id,
        "title": title,
        "summary": {
            "total_assets": total_assets,
            "total_debt": total_debt,
            "net_worth": net_worth,
            "monthly_net_worth": _parse_krw(monthly_kv.get("순자산", dash_kv.get("순자산", 0))),
            "monthly_income": _parse_krw(monthly_kv.get("총 수입", 0)),
            "monthly_expense": _parse_krw(monthly_kv.get("총 지출", 0)),
            "monthly_savings": _parse_krw(monthly_kv.get("순저축", 0)),
            "emergency_months": monthly_kv.get("비상자금 (개월)", ""),
            "goal_progress": dash_kv.get("목표 진행률", ""),
        },
        "by_owner": dict(sorted(by_owner.items(), key=lambda x: -x[1])),
        "by_account": [
            {"account": k[0], "owner": k[1], "type": v["type"], "value": v["value"]}
            for k, v in sorted(by_account.items(), key=lambda x: -x[1]["value"])
            if v["value"] > 0
        ],
        "positions": positions,
        "debts": debts,
    }


def print_report(data: dict) -> None:
    s = data["summary"]
    print(f"\n{'=' * 72}")
    print(f"  {data['title']} — 재무상태 ({data['pulled_at'][:10]})")
    print(f"{'=' * 72}")

    print("\n[핵심 KPI]")
    print(f"  총 자산     {s['total_assets']:>14,}원")
    print(f"  총 부채     {s['total_debt']:>14,}원")
    print(f"  순자산      {s['net_worth']:>14,}원")
    if s["monthly_income"]:
        print(f"  이번달 수입 {s['monthly_income']:>14,}원")
    if s["monthly_expense"]:
        print(f"  이번달 지출 {s['monthly_expense']:>14,}원")
    if s["monthly_savings"]:
        print(f"  이번달 순저축 {s['monthly_savings']:>12,}원")
    if s["emergency_months"]:
        print(f"  비상자금    {s['emergency_months']}")

    print("\n[담당자별 자산]")
    for owner, val in data["by_owner"].items():
        print(f"  {owner:<8} {val:>14,}원")

    print(f"\n[계좌별] ({len(data['by_account'])}개)")
    print(f"{'담당자':<8} {'계좌명':<28} {'유형':<10} {'평가(원)':>14}")
    print("-" * 72)
    for row in data["by_account"]:
        print(f"{row['owner']:<8} {row['account']:<28} {row['type']:<10} {row['value']:>14,}")

    if data["debts"]:
        print(f"\n[부채] ({len(data['debts'])}건)")
        for d in data["debts"]:
            print(f"  {d['type']:<12} {d['name']:<24} {d['balance']:>14,}원")


def main() -> None:
    parser = argparse.ArgumentParser(description="Google 가게부 최신 재무상태 pull")
    parser.add_argument("--id", default=DEFAULT_SPREADSHEET_ID)
    parser.add_argument("--json", dest="json_out", default="", help="JSON 저장 경로")
    args = parser.parse_args()

    try:
        data = pull(args.id)
        print_report(data)
        if args.json_out:
            Path(args.json_out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"\n저장: {args.json_out}")
    except FileNotFoundError as e:
        print(e)
        print(
            "\n=== 1회 설정 ===\n"
            "1. https://console.cloud.google.com/apis/credentials\n"
            "2. OAuth 클라이언트 ID → 데스크톱 앱 → JSON 다운로드\n"
            "3. config/credentials.json 으로 저장 (example 말고 실제 JSON)\n"
            "4. python scripts/pull_financial_status.py\n"
            "   → 브라우저 로그인 → config/token.json 생성\n"
        )
        sys.exit(1)
    except Exception as e:
        print(f"pull 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
