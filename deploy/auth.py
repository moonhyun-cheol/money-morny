"""Google OAuth 2.0 인증."""

from __future__ import annotations

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/script.scriptapp",
]


def get_credentials(config_dir: Path) -> Credentials:
    token_path = config_dir / "token.json"
    creds_path = config_dir / "credentials.json"

    creds: Credentials | None = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError(
                    f"credentials.json이 없습니다: {creds_path}\n"
                    "Google Cloud Console에서 OAuth 클라이언트(데스크톱)를 받아 config/에 저장하세요."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


def build_services(creds: Credentials):
    from googleapiclient.discovery import build

    sheets = build("sheets", "v4", credentials=creds)
    docs = build("docs", "v1", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    script = build("script", "v1", credentials=creds)
    return sheets, docs, drive, script
