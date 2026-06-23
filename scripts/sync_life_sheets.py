#!/usr/bin/env python3
"""기존 재무관리 Google 스프레드시트에 인생라인 탭 3개 추가·갱신."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CONFIG_DIR = ROOT / "config"
SHEET_NAMES = ("인생라인", "라이프페이즈", "분기체크")


def sync(spreadsheet_id: str) -> str:
    from deploy.auth import build_services, get_credentials
    from deploy.sheets_builder import COLORS, _cell, _row_data
    from deploy.sheets_life_line import LIFE_SHEET_IDS, build_life_line_requests, life_sheet_defs

    creds = get_credentials(CONFIG_DIR)
    sheets_svc, _, _, _ = build_services(creds)

    meta = sheets_svc.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta.get("sheets", [])}

    requests: list = []
    for title, default_id in life_sheet_defs():
        if title not in existing:
            requests.append({"addSheet": {"properties": {"title": title, "sheetId": default_id}}})

    if requests:
        sheets_svc.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests},
        ).execute()
        meta = sheets_svc.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        existing = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta.get("sheets", [])}

    sheet_ids = dict(LIFE_SHEET_IDS)
    for key, title in {
        "life_line": "인생라인",
        "life_phase": "라이프페이즈",
        "quarterly": "분기체크",
    }.items():
        if title in existing:
            sheet_ids[key] = existing[title]

    import deploy.sheets_life_line as sl

    sl.LIFE_SHEET_IDS.update(sheet_ids)
    life_reqs = build_life_line_requests(_cell, _row_data, COLORS)
    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": life_reqs},
    ).execute()

    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={existing.get('인생라인', 0)}"


def main() -> None:
    sheet_id = ""
    for arg in sys.argv[1:]:
        if arg.startswith("--id="):
            sheet_id = arg.split("=", 1)[1]

    if not sheet_id:
        print("사용법: python scripts/sync_life_sheets.py --id=스프레드시트ID")
        print("  URL 예: https://docs.google.com/spreadsheets/d/ABC123/edit → ABC123")
        sys.exit(1)

    if not (CONFIG_DIR / "credentials.json").exists():
        print("config/credentials.json 필요 (setup.py deploy와 동일)")
        sys.exit(1)

    url = sync(sheet_id)
    print(f"인생라인 탭 동기화 완료:\n{url}")
    print("\n한눈에보기의 페이즈 수식은 수동으로 갱신하려면 setup.py deploy를 다시 하거나")
    print("한눈에보기 탭을 deploy/sheets_extended.py 내용으로 맞춰 주세요.")


if __name__ == "__main__":
    main()
