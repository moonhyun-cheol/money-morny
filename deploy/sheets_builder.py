"""Google Sheets 재무관리 스프레드시트 생성."""

from __future__ import annotations

from typing import Any

from deploy.sheets_extended import build_asset_rows_extended, build_extended_requests, extended_sheet_defs

SHEET_IDS = {
    "dashboard": 0,
    "settings": 1,
    "assets": 2,
    "expenses": 3,
    "income": 4,
    "monthly": 5,
    "history": 6,
    "quotes": 7,
    "transfers": 8,
    "liabilities": 9,
}

ACCOUNT_TYPES = ["ISA", "주택청약", "연금저축", "IRP", "CMA", "보험", "현금", "적금", "주식", "부동산"]
LIABILITY_TYPES = ["주택담보대출", "신용대출", "마이너스통장", "학자금", "카드할부", "기타"]
TRANSFER_TYPES = [
    "계좌간이동",
    "ISA만기→연금",
    "전량현금화",
    "투자금인출",
    "아파트구매",
    "부채발생",
    "부채상환",
    "종목전환",
]
TRANSFER_STATUS = ["예정", "완료", "취소"]
EXPENSE_CATEGORIES = ["식비", "교통", "쇼핑", "고정비", "의료", "여가", "대출상환", "대출이자", "기타"]
INCOME_TYPES = ["급여", "부수입", "배당", "이자", "기타"]

# 색상 (RGB 0-1)
COLORS = {
    "header": {"red": 0.17, "green": 0.24, "blue": 0.31},
    "header_text": {"red": 1, "green": 1, "blue": 1},
    "kpi_bg": {"red": 0.95, "green": 0.97, "blue": 1},
    "kpi_hero_bg": {"red": 0.88, "green": 0.93, "blue": 0.98},
    "positive": {"red": 0.12, "green": 0.55, "blue": 0.24},
    "negative": {"red": 0.85, "green": 0.19, "blue": 0.15},
    "warning": {"red": 0.98, "green": 0.76, "blue": 0.18},
    "accent": {"red": 0.1, "green": 0.45, "blue": 0.91},
    "bg_ok": {"red": 0.85, "green": 0.95, "blue": 0.85},
    "bg_warn": {"red": 1.0, "green": 0.95, "blue": 0.8},
    "bg_bad": {"red": 0.98, "green": 0.85, "blue": 0.85},
}

# 월 예산 기본값 (설정 시트 초기값)
DEFAULT_BUDGETS: dict[str, int] = {
    "식비": 600_000,
    "교통": 200_000,
    "쇼핑": 300_000,
    "고정비": 500_000,
    "의료": 100_000,
    "여가": 200_000,
    "대출상환": 0,
    "대출이자": 0,
    "기타": 150_000,
}


def create_spreadsheet(sheets_service) -> str:
    """스프레드시트 생성 후 spreadsheetId 반환."""
    body = {
        "properties": {"title": "재무관리", "locale": "ko_KR"},
        "sheets": [
            {"properties": {"sheetId": sid, "title": name, "gridProperties": {"frozenRowCount": 1}}}
            for name, sid in [
                ("대시보드", 0),
                ("설정", 1),
                ("자산_종목", 2),
                ("지출", 3),
                ("수입", 4),
                ("월간집계", 5),
                ("순자산_이력", 6),
                ("시세", 7),
                ("자산_이동", 8),
                ("부채", 9),
                *extended_sheet_defs(),
            ]
        ],
    }
    result = sheets_service.spreadsheets().create(body=body).execute()
    return result["spreadsheetId"]


def _cell(row: int, col: int, value: str | float | int | None = None, formula: str | None = None) -> dict:
    cell: dict[str, Any] = {}
    if formula:
        cell["userEnteredValue"] = {"formulaValue": formula}
    elif value is not None:
        if isinstance(value, (int, float)):
            cell["userEnteredValue"] = {"numberValue": value}
        else:
            cell["userEnteredValue"] = {"stringValue": str(value)}
    return {"values": [cell] if cell else []}


def _row_data(cells: list) -> dict:
    return {"values": cells}


def build_all_updates(spreadsheet_id: str, docs_template_id: str = "") -> list[dict]:
    """batchUpdate 요청 목록 생성."""
    sid = SHEET_IDS
    requests: list[dict] = []

    # ── 설정 시트 ──
    settings_rows = [
        ["항목", "값", "설명"],
        ["Person1 이름", "사람1", "수입·지출 담당자1"],
        ["Person2 이름", "사람2", "수입·지출 담당자2"],
        ["목표 순자산", 100000000, "원 단위"],
        ["목표 날짜", "2030-12-31", "선택"],
        ["추세 계산 개월수", 6, "목표 예측용"],
        ["Docs 템플릿 ID", docs_template_id, "자동 생성됨"],
        ["Drive 폴더 ID", "", "리포트 저장 폴더 (선택)"],
        ["", "", ""],
        ["계좌유형 목록", ", ".join(ACCOUNT_TYPES), ""],
        ["지출 카테고리", ", ".join(EXPENSE_CATEGORIES), ""],
        ["수입 유형", ", ".join(INCOME_TYPES), ""],
        ["", "", ""],
        ["자산 배분 목표(%)", "", "설정!B열에 목표 % 입력"],
    ]
    for acc in ACCOUNT_TYPES:
        settings_rows.append([acc, 0, "목표 비중 %"])
    settings_rows.append(["", "", ""])
    settings_rows.append(["예산 (월 한도)", "", "카테고리별 지출 한도"])
    for cat in EXPENSE_CATEGORIES:
        settings_rows.append([cat, DEFAULT_BUDGETS.get(cat, 0), "원/월"])

    requests.append(
        {
            "updateCells": {
                "range": {"sheetId": sid["settings"], "startRowIndex": 0, "startColumnIndex": 0},
                "rows": [_row_data([_cell(0, j, v) for j, v in enumerate(row)]) for row in settings_rows],
                "fields": "userEnteredValue",
            }
        }
    )

    # ── 자산_종목 (해외·환율 포함) ──
    requests.extend(build_asset_rows_extended(sid["assets"], _cell, _row_data))

    # ── 지출 / 수입 헤더 ──
    requests.append(
        {
            "updateCells": {
                "range": {"sheetId": sid["expenses"], "startRowIndex": 0, "startColumnIndex": 0},
                "rows": [_row_data([_cell(0, j, v) for j, v in enumerate(["날짜", "카테고리", "금액", "메모", "담당자"])])],
                "fields": "userEnteredValue",
            }
        }
    )
    requests.append(
        {
            "updateCells": {
                "range": {"sheetId": sid["income"], "startRowIndex": 0, "startColumnIndex": 0},
                "rows": [_row_data([_cell(0, j, v) for j, v in enumerate(["날짜", "담당자", "유형", "금액", "메모"])])],
                "fields": "userEnteredValue",
            }
        }
    )

    # ── 월간집계 ──
    monthly_formulas: list[tuple | list] = [
        ["월간 집계", "", ""],
        ("집계 연", "=YEAR(TODAY())"),
        ("집계 월", "=MONTH(TODAY())"),
        ["", "", ""],
        ("총 자산", "=SUM('자산_종목'!I2:I500)"),
        ("총 부채", "=SUM('부채'!D2:D200)"),
        ("순자산", "=B5-B6"),
        ("Person1 수입", '=SUMIFS(\'수입\'!D:D,\'수입\'!A:A,">="&DATE(B2,B3,1),\'수입\'!A:A,"<="&EOMONTH(DATE(B2,B3,1),0),\'수입\'!B:B,설정!B2)'),
        ("Person2 수입", '=SUMIFS(\'수입\'!D:D,\'수입\'!A:A,">="&DATE(B2,B3,1),\'수입\'!A:A,"<="&EOMONTH(DATE(B2,B3,1),0),\'수입\'!B:B,설정!B3)'),
        ("총 수입", "=B8+B9"),
        ("총 지출", '=SUMIFS(\'지출\'!C:C,\'지출\'!A:A,">="&DATE(B2,B3,1),\'지출\'!A:A,"<="&EOMONTH(DATE(B2,B3,1),0))'),
        ("순저축", "=B10-B11"),
        ("저축률", '=IF(B10=0,"",B12/B10)'),
        ("비상자금 (개월)", '=IF(B11=0,"",(SUMIF(\'자산_종목\'!A:A,"현금",\'자산_종목\'!I:I)+SUMIF(\'자산_종목\'!A:A,"CMA",\'자산_종목\'!I:I))/B11)'),
    ]
    monthly_rows = []
    for row in monthly_formulas:
        if isinstance(row, tuple) and len(row) == 2:
            monthly_rows.append(_row_data([_cell(0, 0, row[0]), _cell(0, 1, formula=row[1])]))
        else:
            monthly_rows.append(_row_data([_cell(0, j, v if v is not None else "") for j, v in enumerate(row)]))

    # 예산 vs 실적
    monthly_rows.append(_row_data([_cell(0, 0, "")]))
    monthly_rows.append(_row_data([_cell(0, 0, "예산 vs 실적"), _cell(0, 1, "월한도"), _cell(0, 2, "실적"), _cell(0, 3, "달성률")]))
    budget_settings_start = 17 + len(ACCOUNT_TYPES)  # settings row after budgets header
    for i, cat in enumerate(EXPENSE_CATEGORIES):
        r = 17 + i
        settings_r = budget_settings_start + i
        monthly_rows.append(_row_data([
            _cell(0, 0, cat),
            _cell(0, 1, formula=f"=설정!B{settings_r}"),
            _cell(0, 2, formula=(
                f'=SUMIFS(\'지출\'!C:C,\'지출\'!B:B,A{r},'
                f'\'지출\'!A:A,">="&DATE(B2,B3,1),\'지출\'!A:A,"<="&EOMONTH(DATE(B2,B3,1),0))'
            )),
            _cell(0, 3, formula=f'=IF(B{r}=0,"",C{r}/B{r})'),
        ]))

    # 계좌유형별 자산
    monthly_rows.append(_row_data([_cell(0, 0, "")]))
    monthly_rows.append(_row_data([_cell(0, 0, "계좌유형별 자산"), _cell(0, 1, "금액")]))
    asset_block_start = 28
    for i, acc in enumerate(ACCOUNT_TYPES):
        r = asset_block_start + i
        monthly_rows.append(
            _row_data(
                [
                    _cell(0, 0, acc),
                    _cell(0, 1, formula=f"=SUMIF('자산_종목'!A:A,A{r},'자산_종목'!I:I)"),
                ]
            )
        )

    requests.append(
        {
            "updateCells": {
                "range": {"sheetId": sid["monthly"], "startRowIndex": 0, "startColumnIndex": 0},
                "rows": monthly_rows,
                "fields": "userEnteredValue",
            }
        }
    )

    # ── 부채 시트 ──
    liability_headers = [
        "부채유형",
        "부채명",
        "원금",
        "현재잔액",
        "연이자율(%)",
        "월상환액",
        "만기일",
        "연결자산",
        "메모",
    ]
    liability_sample = [
        ["주택담보대출", "○○아파트 담보대출", 300000000, 280000000, 3.5, 1500000, "2055-06-01", "○○아파트", ""],
    ]
    liability_rows = [_row_data([_cell(0, j, v) for j, v in enumerate(liability_headers)])]
    for sample in liability_sample:
        liability_rows.append(_row_data([_cell(0, j, v) for j, v in enumerate(sample)]))

    requests.append(
        {
            "updateCells": {
                "range": {"sheetId": sid["liabilities"], "startRowIndex": 0, "startColumnIndex": 0},
                "rows": liability_rows,
                "fields": "userEnteredValue",
            }
        }
    )

    # ── 자산_이동 시트 ──
    transfer_headers = [
        "날짜",
        "이동유형",
        "출발_계좌유형",
        "출발_계좌명",
        "도착_계좌유형",
        "도착_계좌명",
        "금액",
        "출발_종목명",
        "도착_종목명",
        "부채명(차입시)",
        "메모",
        "상태",
    ]
    transfer_samples = [
        ["2026-06-01", "ISA만기→연금", "ISA", "키움 ISA", "연금저축", "KB 연금저축", 20000000, "", "", "", "ISA 만기 후 연금저축 이전", "예정"],
        ["2026-12-01", "아파트구매", "현금", "주거래", "부동산", "○○아파트", 100000000, "", "○○아파트", "○○아파트 담보대출", "전량 현금화 후 아파트 매입", "예정"],
    ]
    transfer_rows = [_row_data([_cell(0, j, v) for j, v in enumerate(transfer_headers)])]
    for sample in transfer_samples:
        transfer_rows.append(_row_data([_cell(0, j, v) for j, v in enumerate(sample)]))

    # 사용 안내 (1행 아래 주석 대신 헤더 옆 시트 상단에)
    requests.append(
        {
            "updateCells": {
                "range": {"sheetId": sid["transfers"], "startRowIndex": 0, "startColumnIndex": 0},
                "rows": transfer_rows,
                "fields": "userEnteredValue",
            }
        }
    )
    requests.append(
        {
            "updateCells": {
                "range": {"sheetId": sid["transfers"], "startRowIndex": 0, "startColumnIndex": 12, "endRowIndex": 4, "endColumnIndex": 13},
                "rows": [
                    _row_data([_cell(0, 0, "▶ 메뉴: 재무관리 → 자산 이동 실행")]),
                    _row_data([_cell(0, 0, "상태=예정 인 행을 자동 반영")]),
                    _row_data([_cell(0, 0, "아파트구매: 출발=현금, 도착=부동산")]),
                    _row_data([_cell(0, 0, "부채명 열에 대출명 입력")]),
                ],
                "fields": "userEnteredValue",
            }
        }
    )

    # ── 순자산_이력 헤더 ──
    history_headers = [
        "연월",
        "총자산",
        "총부채",
        "순자산",
        "Person1수입",
        "Person2수입",
        "총지출",
        "순저축",
        *ACCOUNT_TYPES,
    ]
    requests.append(
        {
            "updateCells": {
                "range": {"sheetId": sid["history"], "startRowIndex": 0, "startColumnIndex": 0},
                "rows": [_row_data([_cell(0, j, v) for j, v in enumerate(history_headers)])],
                "fields": "userEnteredValue",
            }
        }
    )

    # ── 시세 시트 ──
    requests.append(
        {
            "updateCells": {
                "range": {"sheetId": sid["quotes"], "startRowIndex": 0, "startColumnIndex": 0},
                "rows": [
                    _row_data([_cell(0, j, v) for j, v in enumerate(["종목코드", "종목명", "시장", "현재가", "갱신시각"])]),
                    _row_data(
                        [
                            _cell(0, 0, formula="=UNIQUE(FILTER('자산_종목'!D2:D500,'자산_종목'!D2:D500<>\"\"))"),
                        ]
                    ),
                ],
                "fields": "userEnteredValue",
            }
        }
    )

    # ── 대시보드 (상세 KPI — 허브는 한눈에보기) ──
    dash_rows: list = []
    dash_data: list[tuple | list] = [
        ["📋 상세 KPI", "", "▶ 메인 화면: 한눈에보기 탭"],
        ["", "", ""],
        ("총 자산", "=SUM('자산_종목'!I2:I500)"),
        ("총 부채", "=SUM('부채'!D2:D200)"),
        ("순자산", "=B3-B4"),
        ("전월 순자산 대비", "=IF(COUNT('순자산_이력'!D2:D100)<1,\"-\",B5-INDEX('순자산_이력'!D:D,COUNTA('순자산_이력'!D2:D100)))"),
        ("전월 대비 %", '=IF(B6="-","",IF(INDEX(\'순자산_이력\'!D:D,COUNTA(\'순자산_이력\'!D2:D100))=0,"",B6/INDEX(\'순자산_이력\'!D:D,COUNTA(\'순자산_이력\'!D2:D100))))'),
        ["", "", ""],
        ("이번 달 수입 (합)", "=월간집계!B10"),
        ("  Person1", "=월간집계!B8"),
        ("  Person2", "=월간집계!B9"),
        ("이번 달 지출", "=월간집계!B11"),
        ("순저축", "=월간집계!B12"),
        ("저축률", "=월간집계!B13"),
        ["", "", ""],
        ("부채/자산 비율", '=IF(B3=0,"",B4/B3)'),
        ("목표 순자산", "=설정!B4"),
        ("목표 진행률", '=IF(설정!B4=0,"",B5/설정!B4)'),
        ("예상 달성 (개월)", '=IF(OR(설정!B4=0,COUNT(\'순자산_이력\'!D2:D100)<2),"",MAX(0,(설정!B4-B5)/AVERAGE(OFFSET(\'순자산_이력\'!D2,MAX(0,COUNTA(\'순자산_이력\'!D2:D100)-설정!B6),0,MIN(설정!B6,COUNTA(\'순자산_이력\'!D2:D100)-1),1))))'),
        ("예상 달성 (년)", '=IF(B19="","",B19/12)'),
    ]
    for row in dash_data:
        if isinstance(row, tuple) and len(row) == 2:
            dash_rows.append(_row_data([_cell(0, 0, row[0]), _cell(0, 1, formula=row[1])]))
        else:
            dash_rows.append(_row_data([_cell(0, j, v if v is not None else "") for j, v in enumerate(row)]))

    # 차트용 계좌유형별 (M=12, N=13)
    for i, acc in enumerate(ACCOUNT_TYPES):
        r = 2 + i
        dash_rows.append(
            _row_data(
                [
                    _cell(r - 1, 12, acc),
                    _cell(r - 1, 13, formula=f"=SUMIF('자산_종목'!A:A,M{r},'자산_종목'!I:I)"),
                ]
            )
        )

    # 지출 카테고리 차트 (P=15, Q=16)
    dash_rows.append(_row_data([_cell(0, 14, "카테고리"), _cell(0, 15, "금액")]))
    for i, cat in enumerate(EXPENSE_CATEGORIES):
        r = 13 + i
        dash_rows.append(
            _row_data(
                [
                    _cell(r - 1, 14, cat),
                    _cell(
                        r - 1,
                        15,
                        formula=f'=SUMIFS(\'지출\'!C:C,\'지출\'!B:B,P{r},\'지출\'!A:A,">="&DATE(월간집계!B2,월간집계!B3,1),\'지출\'!A:A,"<="&EOMONTH(DATE(월간집계!B2,월간집계!B3,1),0))',
                    ),
                ]
            )
        )

    requests.append(
        {
            "updateCells": {
                "range": {"sheetId": sid["dashboard"], "startRowIndex": 0, "startColumnIndex": 0},
                "rows": dash_rows,
                "fields": "userEnteredValue",
            }
        }
    )

    requests.extend(_formatting_requests())
    requests.extend(_validation_requests())
    requests.extend(build_extended_requests(sid, _cell, _row_data, ACCOUNT_TYPES, COLORS, EXPENSE_CATEGORIES))
    requests.extend(_ux_requests(sid))

    return requests


def _formatting_requests() -> list[dict]:
    sid = SHEET_IDS
    reqs = []

    header_sheets = [sid["settings"], sid["assets"], sid["expenses"], sid["income"], sid["history"], sid["quotes"], sid["transfers"], sid["liabilities"], sid["monthly"]]
    for sheet_id in header_sheets:
        reqs.append(
            {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": COLORS["header"],
                            "textFormat": {"foregroundColor": COLORS["header_text"], "bold": True},
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            }
        )

    # 설정 시트 — KPI 입력 강조
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sid["settings"], "startRowIndex": 1, "endRowIndex": 8, "startColumnIndex": 0, "endColumnIndex": 3},
            "cell": {"userEnteredFormat": {"backgroundColor": COLORS["kpi_bg"]}},
            "fields": "userEnteredFormat.backgroundColor",
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sid["settings"], "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 3},
            "cell": {"userEnteredFormat": {"textFormat": {"fontSize": 14, "bold": True}}},
            "fields": "userEnteredFormat.textFormat",
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sid["settings"], "startRowIndex": 26, "endRowIndex": 35, "startColumnIndex": 1, "endColumnIndex": 2},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
            "fields": "userEnteredFormat.numberFormat",
        }
    })

    # 대시보드 KPI 영역
    reqs.append(
        {
            "repeatCell": {
                "range": {"sheetId": sid["dashboard"], "startRowIndex": 2, "endRowIndex": 21, "startColumnIndex": 0, "endColumnIndex": 2},
                "cell": {"userEnteredFormat": {"backgroundColor": COLORS["kpi_bg"], "textFormat": {"bold": True}}},
                "fields": "userEnteredFormat(backgroundColor,textFormat)",
            }
        }
    )

    # 금액 포맷
    for sheet_id, col_start, col_end in [
        (sid["assets"], 6, 11),
        (sid["expenses"], 2, 3),
        (sid["income"], 3, 4),
        (sid["liabilities"], 2, 6),
        (sid["transfers"], 6, 7),
        (sid["dashboard"], 1, 2),
    ]:
        reqs.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": 500,
                        "startColumnIndex": col_start,
                        "endColumnIndex": col_end,
                    },
                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
                    "fields": "userEnteredFormat.numberFormat",
                }
            }
        )

    # 비중 % 포맷
    reqs.append(
        {
            "repeatCell": {
                "range": {"sheetId": sid["assets"], "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 10, "endColumnIndex": 11},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}},
                "fields": "userEnteredFormat.numberFormat",
            }
        }
    )

    # 대시보드 진행률 % · 부채비율
    for row_start in [15, 17]:
        reqs.append(
            {
                "repeatCell": {
                    "range": {"sheetId": sid["dashboard"], "startRowIndex": row_start, "endRowIndex": row_start + 1, "startColumnIndex": 1, "endColumnIndex": 2},
                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}},
                    "fields": "userEnteredFormat.numberFormat",
                }
            }
        )

    # 조건부: 전월 순자산 대비
    for cond_type, color in [("NUMBER_GREATER", COLORS["positive"]), ("NUMBER_LESS", COLORS["negative"])]:
        reqs.append(
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{"sheetId": sid["dashboard"], "startRowIndex": 5, "endRowIndex": 6, "startColumnIndex": 1, "endColumnIndex": 2}],
                        "booleanRule": {
                            "condition": {"type": cond_type, "values": [{"userEnteredValue": "0"}]},
                            "format": {"textFormat": {"foregroundColor": color}},
                        },
                    },
                    "index": 0 if cond_type == "NUMBER_GREATER" else 1,
                }
            }
        )

    # 대시보드 제목 (상세 탭)
    reqs.append(
        {
            "repeatCell": {
                "range": {"sheetId": sid["dashboard"], "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 3},
                "cell": {"userEnteredFormat": {"textFormat": {"fontSize": 14, "bold": True, "foregroundColor": COLORS["accent"]}}},
                "fields": "userEnteredFormat.textFormat",
            }
        }
    )

    # 월간집계 — 예산 달성률 %
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sid["monthly"], "startRowIndex": 16, "endRowIndex": 26, "startColumnIndex": 3, "endColumnIndex": 4},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0%"}}},
            "fields": "userEnteredFormat.numberFormat",
        }
    })
    for sh, col in [(sid["monthly"], 1), (sid["monthly"], 2)]:
        reqs.append({
            "repeatCell": {
                "range": {"sheetId": sh, "startRowIndex": 16, "endRowIndex": 26, "startColumnIndex": col, "endColumnIndex": col + 1},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
                "fields": "userEnteredFormat.numberFormat",
            }
        })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sid["monthly"], "startRowIndex": 13, "endRowIndex": 14, "startColumnIndex": 1, "endColumnIndex": 2},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.0"}}},
            "fields": "userEnteredFormat.numberFormat",
        }
    })

    # 틀 고정
    for sheet_id in [sid["assets"], sid["expenses"], sid["income"], sid["history"], sid["transfers"], sid["liabilities"], sid["monthly"]]:
        reqs.append({
            "updateSheetProperties": {
                "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }
        })

    return reqs


def _ux_requests(sid: dict) -> list[dict]:
    """열 너비 · 숨김 · 탭색 · 대시보드 탭 순서."""
    reqs: list[dict] = []

    def col_w(sheet_id: int, start: int, end: int, px: int) -> dict:
        return {
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": start, "endIndex": end},
                "properties": {"pixelSize": px},
                "fields": "pixelSize",
            }
        }

    def hide_cols(sheet_id: int, start: int, end: int) -> dict:
        return {
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": start, "endIndex": end},
                "properties": {"hiddenByUser": True},
                "fields": "hiddenByUser",
            }
        }

    for sheet_id, widths in [
        (sid["assets"], [(0, 1, 90), (1, 2, 140), (2, 3, 80), (3, 4, 70), (4, 5, 120), (8, 9, 110)]),
        (sid["expenses"], [(0, 1, 100), (1, 2, 90), (2, 3, 100), (3, 4, 160), (4, 5, 80)]),
        (sid["income"], [(0, 1, 100), (1, 2, 80), (2, 3, 80), (3, 4, 100), (4, 5, 160)]),
        (sid["settings"], [(0, 1, 160), (1, 2, 140), (2, 3, 220)]),
        (sid["dashboard"], [(0, 1, 180), (1, 2, 140)]),
        (sid["monthly"], [(0, 1, 160), (1, 2, 120), (2, 3, 120), (3, 4, 90)]),
    ]:
        for start, end, px in widths:
            reqs.append(col_w(sheet_id, start, end, px))

    reqs.append(hide_cols(sid["dashboard"], 12, 17))
    reqs.append(hide_cols(10, 25, 30))

    tab_colors = [
        (sid["settings"], {"red": 0.6, "green": 0.6, "blue": 0.65}),
        (sid["assets"], {"red": 0.2, "green": 0.65, "blue": 0.45}),
        (sid["expenses"], {"red": 0.9, "green": 0.45, "blue": 0.4}),
        (sid["income"], {"red": 0.3, "green": 0.7, "blue": 0.5}),
        (sid["monthly"], {"red": 0.55, "green": 0.65, "blue": 0.85}),
        (sid["liabilities"], {"red": 0.85, "green": 0.35, "blue": 0.35}),
        (sid["dashboard"], {"red": 0.75, "green": 0.75, "blue": 0.78}),
    ]
    for sheet_id, color in tab_colors:
        reqs.append({
            "updateSheetProperties": {
                "properties": {"sheetId": sheet_id, "tabColor": color},
                "fields": "tabColor",
            }
        })

    reqs.append({
        "updateSheetProperties": {
            "properties": {"sheetId": sid["dashboard"], "index": 18},
            "fields": "index",
        }
    })

    return reqs


def _validation_requests() -> list[dict]:
    sid = SHEET_IDS
    account_rule = {
        "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in ACCOUNT_TYPES]},
        "showCustomUi": True,
        "strict": False,
    }
    expense_cat_rule = {
        "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in EXPENSE_CATEGORIES]},
        "showCustomUi": True,
        "strict": False,
    }
    income_type_rule = {
        "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in INCOME_TYPES]},
        "showCustomUi": True,
        "strict": False,
    }

    return [
        {
            "setDataValidation": {
                "range": {"sheetId": sid["assets"], "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 0, "endColumnIndex": 1},
                "rule": account_rule,
            }
        },
        {
            "setDataValidation": {
                "range": {"sheetId": sid["expenses"], "startRowIndex": 1, "endRowIndex": 2000, "startColumnIndex": 1, "endColumnIndex": 2},
                "rule": expense_cat_rule,
            }
        },
        {
            "setDataValidation": {
                "range": {"sheetId": sid["income"], "startRowIndex": 1, "endRowIndex": 2000, "startColumnIndex": 2, "endColumnIndex": 3},
                "rule": income_type_rule,
            }
        },
        {
            "setDataValidation": {
                "range": {"sheetId": sid["transfers"], "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 1, "endColumnIndex": 2},
                "rule": {
                    "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in TRANSFER_TYPES]},
                    "showCustomUi": True,
                    "strict": False,
                },
            }
        },
        {
            "setDataValidation": {
                "range": {"sheetId": sid["transfers"], "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 2, "endColumnIndex": 4},
                "rule": account_rule,
            }
        },
        {
            "setDataValidation": {
                "range": {"sheetId": sid["transfers"], "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 4, "endColumnIndex": 6},
                "rule": account_rule,
            }
        },
        {
            "setDataValidation": {
                "range": {"sheetId": sid["transfers"], "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 11, "endColumnIndex": 12},
                "rule": {
                    "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in TRANSFER_STATUS]},
                    "showCustomUi": True,
                    "strict": False,
                },
            }
        },
        {
            "setDataValidation": {
                "range": {"sheetId": sid["liabilities"], "startRowIndex": 1, "endRowIndex": 200, "startColumnIndex": 0, "endColumnIndex": 1},
                "rule": {
                    "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in LIABILITY_TYPES]},
                    "showCustomUi": True,
                    "strict": False,
                },
            }
        },
    ]


def deploy_sheets(sheets_service, docs_template_id: str = "") -> str:
    """스프레드시트 생성 및 설정. spreadsheetId 반환."""
    spreadsheet_id = create_spreadsheet(sheets_service)
    requests = build_all_updates(spreadsheet_id, docs_template_id)

    # 설정 시트 Docs ID 업데이트
    if docs_template_id:
        requests.append(
            {
                "updateCells": {
                    "range": {"sheetId": SHEET_IDS["settings"], "startRowIndex": 6, "startColumnIndex": 1, "endRowIndex": 7, "endColumnIndex": 2},
                    "rows": [_row_data([_cell(0, 0, docs_template_id)])],
                    "fields": "userEnteredValue",
                }
            }
        )

    sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()
    return spreadsheet_id
