"""Apps Script 프로젝트 생성 및 코드 업로드."""

from __future__ import annotations

from pathlib import Path


def _read_script_files(apps_script_dir: Path) -> list[dict]:
    files = []
    order = ["Code.gs", "FxRates.gs", "StockPrice.gs", "AssetTransfer.gs", "TransferTemplates.gs", "MonthlyReport.gs", "DailySnapshot.gs", "Triggers.gs"]
    for name in order:
        path = apps_script_dir / name
        if path.exists():
            files.append({"name": name, "type": "SERVER_JS", "source": path.read_text(encoding="utf-8")})
    return files


def upload_scripts(script_service, spreadsheet_id: str, apps_script_dir: Path) -> str:
    """Spreadsheet에 바인딩된 Apps Script 생성. scriptId 반환."""
    body = {"title": "재무관리 스크립트", "parentId": spreadsheet_id}
    project = script_service.projects().create(body=body).execute()
    script_id = project["scriptId"]

    content = {"files": _read_script_files(apps_script_dir)}
    script_service.projects().updateContent(scriptId=script_id, body=content).execute()
    return script_id
