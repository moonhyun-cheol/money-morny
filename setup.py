#!/usr/bin/env python3
"""재무관리 Google Sheets + Docs 자동 배포."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "config"
APPS_SCRIPT_DIR = ROOT / "apps-script"


def cmd_deploy() -> int:
    sys.path.insert(0, str(ROOT))

    from deploy.auth import build_services, get_credentials
    from deploy.docs_builder import create_report_template
    from deploy.script_uploader import upload_scripts
    from deploy.sheets_builder import deploy_sheets

    print("Google OAuth 인증 중...")
    creds = get_credentials(CONFIG_DIR)
    sheets, docs, drive, script = build_services(creds)

    print("1/4 Google Docs 리포트 템플릿 생성...")
    docs_id = create_report_template(docs)
    print(f"   Docs ID: {docs_id}")

    print("2/4 Google Sheets 스프레드시트 생성...")
    spreadsheet_id = deploy_sheets(sheets, docs_template_id=docs_id)
    sheets_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    docs_url = f"https://docs.google.com/document/d/{docs_id}"
    print(f"   Sheets URL: {sheets_url}")

    print("3/4 Apps Script 업로드...")
    script_id = upload_scripts(script, spreadsheet_id, APPS_SCRIPT_DIR)
    script_url = f"https://script.google.com/home/projects/{script_id}/edit"
    print(f"   Script URL: {script_url}")

    print("4/4 완료!")
    print()
    print("=" * 60)
    print("재무관리 시스템이 생성되었습니다.")
    print("=" * 60)
    print(f"  Spreadsheet : {sheets_url}")
    print(f"  Docs 템플릿 : {docs_url}")
    print(f"  Apps Script : {script_url}")
    print()
    print("다음 단계:")
    print("  1. Spreadsheet URL을 즐겨찾기에 저장")
    print("  2. '설정' 시트 — Person1/Person2 이름, 목표 순자산, 월 예산 한도")
    print("  3. F5 새로고침 → 「재무관리」→「⚙ 트리거 설치 (자동)」")
    print("  4. '자산_종목' — 보유 종목 (C열 담당자 = 설정 이름)")
    print("  5. 「재무관리」→「📊 갱신」→「시세+환율+일별자산」")
    print()
    print("  📖 자세한 설명: docs/사용설명서.md")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="재무관리 Google Workspace 배포")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("deploy", help="Sheets + Docs + Apps Script 일괄 생성")

    args = parser.parse_args()
    if args.command == "deploy":
        return cmd_deploy()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
