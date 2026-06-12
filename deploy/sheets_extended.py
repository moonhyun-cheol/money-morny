"""확장 시트: UX 패널, 세금한도, 만기, DSR, 시나리오, 환율, 이동템플릿 + 차트."""

from __future__ import annotations

from typing import Any, Callable

EXT_SHEET_IDS = {
    "visual": 10,
    "tax_limits": 11,
    "maturity": 12,
    "dsr": 13,
    "scenario": 14,
    "fx": 15,
    "transfer_tpl": 16,
    "account_list": 17,
    "daily_assets": 18,
}

PERSON_OPTIONS = ["사람1", "사람2", "공동"]

MARKETS = ["KS", "KQ", "US", "CN", ""]
CURRENCIES = ["KRW", "USD", "CNY"]

TAX_LIMITS = [
    ("ISA", 20_000_000, "연 납입 한도"),
    ("연금저축", 6_000_000, "세액공제 납입한도(연)"),
    ("IRP", 9_000_000, "세액공제 합산 참고"),
    ("주택청약", 2_400_000, "월 20만×12 (전세대략)"),
]

TRANSFER_TEMPLATES = [
    ["ISA만기→연금", "ISA만기→연금", "ISA", "키움 ISA", "연금저축", "KB 연금저축", "ISA 만기 자금 이동"],
    ["전량현금화", "전량현금화", "ISA", "키움 ISA", "현금", "주거래", "투자금 전량 인출"],
    ["CMA→IRP", "계좌간이동", "CMA", "CMA", "IRP", "IRP", "월 추가 납입"],
    ["아파트자기자금", "아파트구매", "현금", "주거래", "부동산", "○○아파트", "담보대출은 부채 시트"],
]


def extended_sheet_defs() -> list[tuple[str, int]]:
    return [
        ("한눈에보기", 10),
        ("세금한도", 11),
        ("만기_캘린더", 12),
        ("DSR_상환", 13),
        ("시나리오", 14),
        ("환율", 15),
        ("이동_템플릿", 16),
        ("계좌목록", 17),
        ("자산_일별이력", 18),
    ]


def build_asset_rows_extended(
    sid_assets: int,
    _cell: Callable,
    _row_data: Callable,
) -> list[dict]:
    """자산_종목 — 담당자·해외·환율 (A~O)."""
    headers = [
        "계좌유형", "계좌명", "담당자", "티커", "종목명", "수량", "평단가", "현재가",
        "평가금액(원)", "평가손익(원)", "비중%", "시장", "통화", "적용환율",
    ]
    samples = [
        ["ISA", "사람1-키움ISA", "사람1", "VOO", "Vanguard S&P500", 10, 450, 480, None, None, None, "US", "USD", None],
        ["적금", "사람1-KB적금", "사람1", "", "KB적금", 1, 0, 5000000, None, None, None, "", "KRW", None],
        ["적금", "사람2-신한적금", "사람2", "", "신한적금", 1, 0, 3000000, None, None, None, "", "KRW", None],
        ["ISA", "사람2-키움ISA", "사람2", "005930", "삼성전자", 5, 70000, 75000, None, None, None, "KS", "KRW", None],
    ]

    def fx_formula(r: int) -> str:
        return f'=IF(M{r}="KRW",1,IF(M{r}="USD",\'환율\'!$B$2,IF(M{r}="CNY",\'환율\'!$B$3,1)))'

    rows = [_row_data([_cell(0, j, v) for j, v in enumerate(headers)])]
    for r, sample in enumerate(samples, start=2):
        cells = [_cell(r - 1, j, v) for j, v in enumerate(sample)]
        cells[13] = _cell(r - 1, 13, formula=fx_formula(r))
        cells[8] = _cell(r - 1, 8, formula=f'=IF(F{r}="","",F{r}*H{r}*N{r})')
        cells[9] = _cell(r - 1, 9, formula=f'=IF(OR(F{r}="",G{r}=""),"",(H{r}-G{r})*F{r}*N{r})')
        cells[10] = _cell(
            r - 1, 10,
            formula=f'=IF(I{r}="","",IF(SUM(\'자산_종목\'!$I$2:$I$500)=0,"",I{r}/SUM(\'자산_종목\'!$I$2:$I$500)))',
        )
        rows.append(_row_data(cells))

    for r in range(len(samples) + 2, 51):
        cells = [_cell(r - 1, j, "") for j in range(14)]
        cells[13] = _cell(r - 1, 13, formula=fx_formula(r))
        cells[8] = _cell(r - 1, 8, formula=f'=IF(F{r}="","",F{r}*H{r}*N{r})')
        cells[9] = _cell(r - 1, 9, formula=f'=IF(OR(F{r}="",G{r}=""),"",(H{r}-G{r})*F{r}*N{r})')
        cells[10] = _cell(
            r - 1, 10,
            formula=f'=IF(I{r}="","",IF(SUM(\'자산_종목\'!$I$2:$I$500)=0,"",I{r}/SUM(\'자산_종목\'!$I$2:$I$500)))',
        )
        rows.append(_row_data(cells))

    return [{
        "updateCells": {
            "range": {"sheetId": sid_assets, "startRowIndex": 0, "startColumnIndex": 0, "endRowIndex": 50, "endColumnIndex": 14},
            "rows": rows,
            "fields": "userEnteredValue",
        }
    }]


def build_extended_requests(
    sid: dict,
    _cell: Callable,
    _row_data: Callable,
    ACCOUNT_TYPES: list[str],
    COLORS: dict,
    EXPENSE_CATEGORIES: list[str] | None = None,
) -> list[dict]:
    ex = EXT_SHEET_IDS
    reqs: list[dict] = []

    # ── 환율 ──
    fx_rows = [
        ["통화", "KRW 환율", "설명", "갱신시각"],
        ["USD", 1350, "1 USD → KRW (Yahoo USDKRW=X)", ""],
        ["CNY", 186, "1 CNY(위안) → KRW (USDKRW÷USDCNY)", ""],
        ["", "", "▶ 메뉴 「시세+환율 갱신」 또는 매일 09:00 자동", ""],
    ]
    reqs.append(_cells(ex["fx"], fx_rows, _cell, _row_data))

    # ── 세금한도 ──
    tax_rows = [["계좌", "연간한도", "올해납입", "잔여", "사용률", "상태", "메모"]]
    for i, (name, limit, note) in enumerate(TAX_LIMITS, start=2):
        r = i
        if name == "ISA":
            ytd = '=SUMIFS(\'자산_이동\'!G:G,\'자산_이동\'!E:E,"ISA",\'자산_이동\'!A:A,">="&DATE(YEAR(TODAY()),1,1),\'자산_이동\'!L:L,"완료")'
        elif name in ("연금저축", "IRP"):
            ytd = f'=SUMIFS(\'자산_이동\'!G:G,\'자산_이동\'!E:E,"{name}",\'자산_이동\'!A:A,">="&DATE(YEAR(TODAY()),1,1),\'자산_이동\'!L:L,"완료")'
        else:
            ytd = 0
        tax_rows.append([name, limit, ytd if isinstance(ytd, str) else ytd, None, None, None, note])
    tax_data = [_row_data([_cell(0, j, v) for j, v in enumerate(tax_rows[0])])]
    for i, row in enumerate(tax_rows[1:], start=2):
        tax_data.append(_row_data([
            _cell(i - 1, 0, row[0]),
            _cell(i - 1, 1, row[1]),
            _cell(i - 1, 2, formula=row[2]) if isinstance(row[2], str) else _cell(i - 1, 2, row[2]),
            _cell(i - 1, 3, formula=f"=MAX(0,B{i}-C{i})"),
            _cell(i - 1, 4, formula=f'=IF(B{i}=0,"",C{i}/B{i})'),
            _cell(i - 1, 5, formula=f'=IF(E{i}>=1,"🔴 초과",IF(E{i}>=0.8,"🟡 임박","🟢 여유"))'),
            _cell(i - 1, 6, row[6]),
        ]))
    reqs.append({"updateCells": {"range": {"sheetId": ex["tax_limits"], "startRowIndex": 0}, "rows": tax_data, "fields": "userEnteredValue"}})

    # ── 만기 캘린더 ──
    mat_rows = [
        ["계좌유형", "계좌명", "상품명", "만기일", "D-day", "예상금액", "알림", "메모"],
        ["ISA", "키움 ISA", "3년만기", "2026-12-31", None, 15000000, None, "연금 이전 예정"],
        ["적금", "KB 적금", "1년", "2026-08-15", None, 12000000, None, ""],
    ]
    mat_data = [_row_data([_cell(0, j, v) for j, v in enumerate(mat_rows[0])])]
    for i, row in enumerate(mat_rows[1:], start=2):
        mat_data.append(_row_data([
            _cell(i - 1, 0, row[0]), _cell(i - 1, 1, row[1]), _cell(i - 1, 2, row[2]),
            _cell(i - 1, 3, row[3]),
            _cell(i - 1, 4, formula=f'=IF(D{i}="","",D{i}-TODAY())'),
            _cell(i - 1, 5, row[5]),
            _cell(i - 1, 6, formula=f'=IF(E{i}="","",IF(E{i}<=30,"⚠️ 임박","✓"))'),
            _cell(i - 1, 7, row[7]),
        ]))
    reqs.append({"updateCells": {"range": {"sheetId": ex["maturity"], "startRowIndex": 0}, "rows": mat_data, "fields": "userEnteredValue"}})

    # ── DSR / 상환 ──
    dsr_rows: list[tuple | list] = [
        ["DSR · 상환 부담 분석", "", "", ""],
        ("연간 세전소득 (2인)", '=SUMIFS(\'수입\'!D:D,\'수입\'!A:A,">="&DATE(YEAR(TODAY())-1,MONTH(TODAY()),DAY(TODAY())))', "최근 12개월"),
        ("연간 원리금 상환", "=SUM('부채'!F:F)*12", "월상환×12"),
        ("DSR (%)", "=IF(B2=0,\"\",B3/B2)", "40% 이하 권장"),
        ("DSR 상태", '=IF(B4="","",IF(B4>0.4,"🔴 주의",IF(B4>0.3,"🟡 보통","🟢 양호")))', ""),
        ("월 가용여력", "=B2/12-SUM('부채'!F:F)-월간집계!B11", "소득-대출-지출"),
        ["", "", "", ""],
        ["부채별 상환 요약", "잔액", "월상환", "연상환", "만기"],
    ]
    dsr_data = []
    for row in dsr_rows:
        if isinstance(row, tuple) and len(row) >= 2 and str(row[1]).startswith("="):
            dsr_data.append(_row_data([
                _cell(0, 0, row[0]),
                _cell(0, 1, formula=row[1]),
                _cell(0, 2, row[2] if len(row) > 2 else ""),
            ]))
        elif isinstance(row, list):
            dsr_data.append(_row_data([_cell(0, j, v if v is not None else "") for j, v in enumerate(row)]))
    for br in range(2, 12):
        out_r = br + 7
        dsr_data.append(_row_data([
            _cell(out_r - 1, 0, formula=f"=IF('부채'!B{br}=\"\",\"\",'부채'!B{br})"),
            _cell(out_r - 1, 1, formula=f"=IF('부채'!D{br}=\"\",\"\",'부채'!D{br})"),
            _cell(out_r - 1, 2, formula=f"=IF('부채'!F{br}=\"\",\"\",'부채'!F{br})"),
            _cell(out_r - 1, 3, formula=f"=IF(C{out_r}=\"\",\"\",C{out_r}*12)"),
            _cell(out_r - 1, 4, formula=f"=IF('부채'!G{br}=\"\",\"\",'부채'!G{br})"),
        ]))
    reqs.append({"updateCells": {"range": {"sheetId": ex["dsr"], "startRowIndex": 0}, "rows": dsr_data, "fields": "userEnteredValue"}})

    # ── 시나리오 ──
    sc = ex["scenario"]
    sc_rows = [
        ["시나리오 비교 (순자산 예측)", "", "", ""],
        ["항목", "A: 지금 매매", "B: 1년 후", "차이(B-A)"],
        ["월 저축액", 3000000, 3000000, None],
        ["연 수익률", 0.07, 0.07, None],
        ["일회성 지출", 500000000, 0, None],
        ["지출 시점(개월 후)", 0, 12, None],
        ["예측 기간(개월)", 60, 60, ""],
        ["", "", "", ""],
        ["월", "순자산 A", "순자산 B", ""],
    ]
    sc_data = [_row_data([_cell(0, j, v if v is not None else "") for j, v in enumerate(sc_rows[0])])]
    for row in sc_rows[1:7]:
        sc_data.append(_row_data([_cell(0, j, v if v is not None else "") for j, v in enumerate(row)]))
    sc_data[2] = _row_data([_cell(0, 0, "월 저축액"), _cell(0, 1, 3000000), _cell(0, 2, 3000000), _cell(0, 3, formula="=C3-B3")])
    sc_data[3] = _row_data([_cell(0, 0, "연 수익률"), _cell(0, 1, 0.07), _cell(0, 2, 0.07), _cell(0, 3, formula="=C4-B4")])
    sc_data[4] = _row_data([_cell(0, 0, "일회성 지출"), _cell(0, 1, 500000000), _cell(0, 2, 0), _cell(0, 3, formula="=C5-B5")])
    sc_data[5] = _row_data([_cell(0, 0, "지출 시점(개월)"), _cell(0, 1, 0), _cell(0, 2, 12), _cell(0, 3, formula="=C6-B6")])
    sc_data.append(_row_data([_cell(0, 0, "월"), _cell(0, 1, "순자산 A"), _cell(0, 2, "순자산 B"), _cell(0, 3, "차이")]))
    for m in range(0, 61):
        r = 10 + m  # sheet row 10 = month 0
        if m == 0:
            fa, fb = "='대시보드'!B5", "='대시보드'!B5"
        else:
            prev = r - 1
            fa = f"=MAX(0,B{prev}*(1+$B$4/12)+$B$3-IF($B$6={m},$B$5,0))"
            fb = f"=MAX(0,C{prev}*(1+$C$4/12)+$C$3-IF($C$6={m},$C$5,0))"
        sc_data.append(_row_data([
            _cell(r - 1, 0, m),
            _cell(r - 1, 1, formula=fa),
            _cell(r - 1, 2, formula=fb),
            _cell(r - 1, 3, formula=f"=C{r}-B{r}"),
        ]))
    reqs.append({"updateCells": {"range": {"sheetId": sc, "startRowIndex": 0}, "rows": sc_data, "fields": "userEnteredValue"}})

    # ── 이동 템플릿 ──
    tpl_headers = ["템플릿명", "이동유형", "출발_유형", "출발_명", "도착_유형", "도착_명", "메모"]
    tpl_data = [_row_data([_cell(0, j, v) for j, v in enumerate(tpl_headers)])]
    for row in TRANSFER_TEMPLATES:
        tpl_data.append(_row_data([_cell(0, j, v) for j, v in enumerate(row)]))
    tpl_data.append(_row_data([_cell(0, 0, "▶ 메뉴: 재무관리 → 템플릿 적용 (행번호 입력)")]))
    reqs.append({"updateCells": {"range": {"sheetId": ex["transfer_tpl"], "startRowIndex": 0}, "rows": tpl_data, "fields": "userEnteredValue"}})

    # ── 계좌목록 (QUERY 자동 집계) ──
    acct = ex["account_list"]
    acct_rows = [
        ["📋 계좌목록 — 담당자·통장별 자동 집계", "", "", "", "", ""],
        ["아래 표는 자산_종목에서 자동 생성됩니다. 통장 추가 후 새로고침(F5) 하세요.", "", "", "", "", ""],
        ["담당자", "계좌유형", "계좌명", "종목수", "총평가(원)", "비중%"],
    ]
    acct_data = [_row_data([_cell(0, j, v) for j, v in enumerate(row)]) for row in acct_rows]
    acct_data.append(_row_data([_cell(0, 0, formula=(
        '=QUERY(\'자산_종목\'!A2:O500, '
        '"select C, A, B, count(D), sum(I) '
        'where C is not null and I is not null '
        'group by C, A, B '
        'order by C, A, B '
        'label count(D) \'종목수\', sum(I) \'총평가\'", 1)'
    ))]))
    reqs.append({"updateCells": {"range": {"sheetId": acct, "startRowIndex": 0}, "rows": acct_data, "fields": "userEnteredValue"}})
    reqs.append({
        "updateCells": {
            "range": {"sheetId": acct, "startRowIndex": 3, "startColumnIndex": 5, "endRowIndex": 4, "endColumnIndex": 6},
            "rows": [_row_data([_cell(0, 0, formula='=ARRAYFORMULA(IF(E4:E500="","",E4:E500/SUM(E4:E500)))')])],
            "fields": "userEnteredValue",
        }
    })
    reqs.append({
        "updateCells": {
            "range": {"sheetId": acct, "startRowIndex": 0, "startColumnIndex": 7, "endRowIndex": 5, "endColumnIndex": 9},
            "rows": [
                _row_data([_cell(0, 0, "담당자별 합계"), _cell(0, 1, "금액(원)")]),
                _row_data([_cell(0, 0, formula="=설정!B2"), _cell(0, 1, formula="=SUMIF('자산_종목'!C:C,설정!B2,'자산_종목'!I:I)")]),
                _row_data([_cell(0, 0, formula="=설정!B3"), _cell(0, 1, formula="=SUMIF('자산_종목'!C:C,설정!B3,'자산_종목'!I:I)")]),
                _row_data([_cell(0, 0, "공동"), _cell(0, 1, formula='=SUMIF(\'자산_종목\'!C:C,"공동",\'자산_종목\'!I:I)')]),
            ],
            "fields": "userEnteredValue",
        }
    })
    p2_type_rows = []  # 계좌목록 — 표만 (차트 제거)

    # ── 자산_일별이력 (담당자별·합계 일별 추적) ──
    daily = ex["daily_assets"]
    daily_data = [
        _row_data([_cell(0, 0, "📈 자산 일별 이력 — 담당자별·2인 합계")]),
        _row_data([_cell(0, 0, "매일 09:00 시세 갱신 후 자동 기록 · 오늘 날짜는 최신값으로 덮어씀")]),
        _row_data([
            _cell(0, 0, "날짜"),
            _cell(0, 1, formula='=설정!B2&" 자산"'),
            _cell(0, 2, formula='=설정!B3&" 자산"'),
            _cell(0, 3, "공동"),
            _cell(0, 4, "합계(2인+공동)"),
        ]),
    ]
    reqs.append({"updateCells": {"range": {"sheetId": daily, "startRowIndex": 0}, "rows": daily_data, "fields": "userEnteredValue"}})
    reqs.append({
        "updateSheetProperties": {
            "properties": {"sheetId": daily, "gridProperties": {"frozenRowCount": 3}},
            "fields": "gridProperties.frozenRowCount",
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": daily, "startRowIndex": 3, "endRowIndex": 400, "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}}},
            "fields": "userEnteredFormat.numberFormat",
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": daily, "startRowIndex": 3, "endRowIndex": 400, "startColumnIndex": 1, "endColumnIndex": 5},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
            "fields": "userEnteredFormat.numberFormat",
        }
    })

    # ── 한눈에보기 (UX 허브 — 단일 진입점) ──
    vis = ex["visual"]
    nav_links = [
        ('=HYPERLINK("#gid=2","📊 자산")', '=HYPERLINK("#gid=3","💸 지출")', '=HYPERLINK("#gid=4","💰 수입")'),
        ('=HYPERLINK("#gid=9","🏦 부채")', '=HYPERLINK("#gid=18","📈 일별추이")', '=HYPERLINK("#gid=0","📋 상세KPI")'),
        ('=HYPERLINK("#gid=11","세금")', '=HYPERLINK("#gid=13","DSR")', '=HYPERLINK("#gid=14","시나리오")'),
    ]
    vis_data = [
        _row_data([_cell(0, 0, "✦ 재무관리 한눈에 보기")]),
        _row_data([_cell(0, 0, formula=nav_links[0][0]), _cell(0, 1, formula=nav_links[0][1]), _cell(0, 2, formula=nav_links[0][2])]),
        _row_data([_cell(0, 0, formula=nav_links[1][0]), _cell(0, 1, formula=nav_links[1][1]), _cell(0, 2, formula=nav_links[1][2])]),
        _row_data([_cell(0, 0, formula=nav_links[2][0]), _cell(0, 1, formula=nav_links[2][1]), _cell(0, 2, formula=nav_links[2][2])]),
        _row_data([_cell(0, 0, "💡 매일: 지출·수입  |  주 1회: 메뉴 → 시세+환율 갱신")]),
        _row_data([_cell(0, 0, "핵심 지표"), _cell(0, 1, "값"), _cell(0, 2, "상태")]),
        _row_data([
            _cell(0, 0, "순자산"),
            _cell(0, 1, formula="='대시보드'!B5"),
            _cell(0, 2, formula='=IF(\'대시보드\'!B6="-","",IF(\'대시보드\'!B6>0,"▲ 전월比","▼ 전월比"))'),
        ]),
        _row_data([
            _cell(0, 0, "순저축 (이번 달)"),
            _cell(0, 1, formula="=월간집계!B12"),
            _cell(0, 2, formula='=IF(월간집계!B13="","",TEXT(월간집계!B13,"0%")&" 저축률")'),
        ]),
        _row_data([
            _cell(0, 0, "DSR"),
            _cell(0, 1, formula="='DSR_상환'!B4"),
            _cell(0, 2, formula="='DSR_상환'!B5"),
        ]),
        _row_data([
            _cell(0, 0, "목표 진행률"),
            _cell(0, 1, formula="='대시보드'!B18"),
            _cell(0, 2, formula='=IF(\'대시보드\'!B19="","",\'대시보드\'!B19&"개월 예상")'),
        ]),
        _row_data([
            _cell(0, 0, "비상자금"),
            _cell(0, 1, formula="=월간집계!B14"),
            _cell(0, 2, formula='=IF(월간집계!B14="","","개월 버틸 수 있음")'),
        ]),
    ]
    reqs.append({"updateCells": {"range": {"sheetId": vis, "startRowIndex": 0, "startColumnIndex": 0}, "rows": vis_data, "fields": "userEnteredValue"}})

    # 차트용 숨김 데이터 (Z~AB 열, row 10~13)
    hidden_person = [
        _row_data([_cell(0, 0, "담당자"), _cell(0, 1, "자산(원)")]),
        _row_data([_cell(0, 0, formula="=설정!B2"), _cell(0, 1, formula="=SUMIF('자산_종목'!C:C,설정!B2,'자산_종목'!I:I)")]),
        _row_data([_cell(0, 0, formula="=설정!B3"), _cell(0, 1, formula="=SUMIF('자산_종목'!C:C,설정!B3,'자산_종목'!I:I)")]),
        _row_data([_cell(0, 0, "공동"), _cell(0, 1, formula='=SUMIF(\'자산_종목\'!C:C,"공동",\'자산_종목\'!I:I)')]),
    ]
    reqs.append({
        "updateCells": {
            "range": {"sheetId": vis, "startRowIndex": 9, "startColumnIndex": 25, "endRowIndex": 13, "endColumnIndex": 27},
            "rows": hidden_person,
            "fields": "userEnteredValue",
        }
    })

    # ── 서식 · 유효성 · 차트 ──
    reqs.extend(_extended_formatting(ex, COLORS))
    reqs.extend(_extended_conditional_formatting(ex, COLORS))
    reqs.extend(_extended_validation(ex, MARKETS, CURRENCIES))
    reqs.extend(_extended_charts(ex, sid))
    reqs.append({
        "updateSheetProperties": {
            "properties": {"sheetId": ex["visual"], "index": 0, "tabColor": {"red": 0.2, "green": 0.45, "blue": 0.75}},
            "fields": "index,tabColor",
        }
    })
    for sheet_id, color in [
        (ex["tax_limits"], {"red": 0.95, "green": 0.85, "blue": 0.3}),
        (ex["maturity"], {"red": 0.85, "green": 0.5, "blue": 0.9}),
        (ex["dsr"], {"red": 0.9, "green": 0.4, "blue": 0.4}),
        (ex["scenario"], {"red": 0.4, "green": 0.7, "blue": 0.5}),
        (ex["fx"], {"red": 0.3, "green": 0.6, "blue": 0.85}),
        (ex["account_list"], {"red": 0.55, "green": 0.75, "blue": 0.55}),
        (ex["daily_assets"], {"red": 0.35, "green": 0.55, "blue": 0.85}),
    ]:
        reqs.append({
            "updateSheetProperties": {
                "properties": {"sheetId": sheet_id, "tabColor": color},
                "fields": "tabColor",
            }
        })

    return reqs


def _cells(sheet_id: int, rows: list, _cell, _row_data) -> dict:
    return {
        "updateCells": {
            "range": {"sheetId": sheet_id, "startRowIndex": 0, "startColumnIndex": 0},
            "rows": [_row_data([_cell(0, j, v) for j, v in enumerate(row)]) for row in rows],
            "fields": "userEnteredValue",
        }
    }


def _extended_formatting(ex: dict, COLORS: dict) -> list[dict]:
    reqs = []
    for sheet_id in [ex["tax_limits"], ex["maturity"], ex["dsr"], ex["scenario"], ex["fx"], ex["transfer_tpl"], ex["visual"], ex["account_list"], ex["daily_assets"]]:
        reqs.append({
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {"backgroundColor": COLORS["header"], "textFormat": {"foregroundColor": COLORS["header_text"], "bold": True}}},
                "fields": "userEnteredFormat(backgroundColor,textFormat)",
            }
        })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": ex["visual"], "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 4},
            "cell": {"userEnteredFormat": {"textFormat": {"fontSize": 16, "bold": True, "foregroundColor": COLORS["accent"]}}},
            "fields": "userEnteredFormat.textFormat",
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": ex["visual"], "startRowIndex": 1, "endRowIndex": 4, "startColumnIndex": 0, "endColumnIndex": 3},
            "cell": {"userEnteredFormat": {"textFormat": {"fontSize": 11, "foregroundColor": COLORS["accent"]}}},
            "fields": "userEnteredFormat.textFormat",
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": ex["visual"], "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": 3},
            "cell": {"userEnteredFormat": {"textFormat": {"fontSize": 10, "foregroundColor": COLORS["accent"]}}},
            "fields": "userEnteredFormat.textFormat",
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": ex["visual"], "startRowIndex": 5, "endRowIndex": 6, "startColumnIndex": 0, "endColumnIndex": 3},
            "cell": {"userEnteredFormat": {"backgroundColor": COLORS["header"], "textFormat": {"foregroundColor": COLORS["header_text"], "bold": True}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": ex["visual"], "startRowIndex": 7, "endRowIndex": 8, "startColumnIndex": 0, "endColumnIndex": 3},
            "cell": {"userEnteredFormat": {"backgroundColor": COLORS["kpi_hero_bg"], "textFormat": {"bold": True, "fontSize": 18}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": ex["visual"], "startRowIndex": 8, "endRowIndex": 12, "startColumnIndex": 0, "endColumnIndex": 3},
            "cell": {"userEnteredFormat": {"backgroundColor": COLORS["kpi_bg"], "textFormat": {"bold": True, "fontSize": 12}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": ex["visual"], "startRowIndex": 7, "endRowIndex": 8, "startColumnIndex": 1, "endColumnIndex": 2},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
            "fields": "userEnteredFormat.numberFormat",
        }
    })
    for sh, cols in [(ex["tax_limits"], (1, 5)), (ex["dsr"], (1, 4)), (ex["scenario"], (1, 4)), (ex["fx"], (1, 2))]:
        reqs.append({
            "repeatCell": {
                "range": {"sheetId": sh, "startRowIndex": 1, "endRowIndex": 100, "startColumnIndex": cols[0], "endColumnIndex": cols[1]},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
                "fields": "userEnteredFormat.numberFormat",
            }
        })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": ex["tax_limits"], "startRowIndex": 1, "endRowIndex": 10, "startColumnIndex": 4, "endColumnIndex": 5},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0%"}}},
            "fields": "userEnteredFormat.numberFormat",
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": ex["dsr"], "startRowIndex": 3, "endRowIndex": 4, "startColumnIndex": 1, "endColumnIndex": 2},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}},
            "fields": "userEnteredFormat.numberFormat",
        }
    })
    return reqs


def _extended_conditional_formatting(ex: dict, COLORS: dict) -> list[dict]:
    """세금한도·DSR·월간 예산 — 배경색 경고."""
    tax = ex["tax_limits"]
    dsr = ex["dsr"]
    monthly = 5

    def cf_range(sheet_id, r1, r2, c1, c2, formula, bg):
        return {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}],
                    "booleanRule": {
                        "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": formula}]},
                        "format": {"backgroundColor": bg},
                    },
                },
                "index": 0,
            }
        }

    rules = [
        cf_range(tax, 1, 5, 4, 5, "=$E2>=1", COLORS["bg_bad"]),
        cf_range(tax, 1, 5, 4, 5, "=AND($E2>=0.8,$E2<1)", COLORS["bg_warn"]),
        cf_range(tax, 1, 5, 4, 5, "=$E2<0.8", COLORS["bg_ok"]),
        cf_range(dsr, 3, 4, 1, 2, "=$B$4>0.4", COLORS["bg_bad"]),
        cf_range(dsr, 3, 4, 1, 2, "=AND($B$4>0.3,$B$4<=0.4)", COLORS["bg_warn"]),
        cf_range(dsr, 3, 4, 1, 2, "=$B$4<=0.3", COLORS["bg_ok"]),
        cf_range(monthly, 16, 25, 3, 4, "=$D17>1", COLORS["bg_bad"]),
        cf_range(monthly, 16, 25, 3, 4, "=AND($D17>=0.8,$D17<=1)", COLORS["bg_warn"]),
    ]
    return rules


def _extended_validation(ex: dict, MARKETS: list, CURRENCIES: list) -> list[dict]:
    market_rule = {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in MARKETS]}, "showCustomUi": True, "strict": False}
    currency_rule = {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in CURRENCIES]}, "showCustomUi": True, "strict": False}
    person_rule = {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in PERSON_OPTIONS]}, "showCustomUi": True, "strict": False}
    return [
        {"setDataValidation": {"range": {"sheetId": 2, "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 2, "endColumnIndex": 3}, "rule": person_rule}},
        {"setDataValidation": {"range": {"sheetId": 2, "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 11, "endColumnIndex": 12}, "rule": market_rule}},
        {"setDataValidation": {"range": {"sheetId": 2, "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 12, "endColumnIndex": 13}, "rule": currency_rule}},
    ]


def _extended_charts(ex: dict, sid: dict) -> list[dict]:
    vis = ex["visual"]
    tax = ex["tax_limits"]
    sc = ex["scenario"]
    mat = ex["maturity"]
    daily = ex["daily_assets"]
    monthly = sid["monthly"]
    hist = sid["history"]

    def sr(sheet_id, r1, r2, c1, c2):
        return {"sources": [{"sheetId": sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}]}

    daily_growth_chart = {
        "title": "일별 자산 추이 (담당자·합계)",
        "basicChart": {
            "chartType": "LINE",
            "legendPosition": "BOTTOM_LEGEND",
            "axis": [
                {"position": "BOTTOM_AXIS", "title": "날짜"},
                {"position": "LEFT_AXIS", "title": "원"},
            ],
            "domains": [{"domain": {"sourceRange": sr(daily, 2, 400, 0, 1)}}],
            "series": [
                {"series": {"sourceRange": sr(daily, 2, 400, 1, 2)}, "targetAxis": "LEFT_AXIS"},
                {"series": {"sourceRange": sr(daily, 2, 400, 2, 3)}, "targetAxis": "LEFT_AXIS"},
                {"series": {"sourceRange": sr(daily, 2, 400, 4, 5)}, "targetAxis": "LEFT_AXIS"},
            ],
            "headerCount": 1,
        },
    }

    return [
        # 한눈에보기: 담당자별 자산 (도넛 1개)
        {"addChart": {"chart": {"spec": {"title": "담당자별 자산", "pieChart": {
            "legendPosition": "LABELED_LEGEND",
            "domain": {"sourceRange": sr(vis, 10, 13, 25, 26)},
            "series": {"sourceRange": sr(vis, 10, 13, 26, 27)},
            "pieHole": 0.45,
        }}, "position": {"overlayPosition": {"anchorCell": {"sheetId": vis, "rowIndex": 12, "columnIndex": 0}, "widthPixels": 380, "heightPixels": 300}}}}},
        # 한눈에보기: 예산 vs 실적
        {"addChart": {"chart": {"spec": {"title": "예산 vs 실적 (이번 달)", "basicChart": {
            "chartType": "COLUMN", "legendPosition": "BOTTOM_LEGEND",
            "axis": [{"position": "BOTTOM_AXIS"}, {"position": "LEFT_AXIS", "title": "원"}],
            "domains": [{"domain": {"sourceRange": sr(monthly, 15, 25, 0, 1)}}],
            "series": [
                {"series": {"sourceRange": sr(monthly, 15, 25, 1, 2)}, "targetAxis": "LEFT_AXIS"},
                {"series": {"sourceRange": sr(monthly, 15, 25, 2, 3)}, "targetAxis": "LEFT_AXIS"},
            ],
            "headerCount": 1,
        }}, "position": {"overlayPosition": {"anchorCell": {"sheetId": vis, "rowIndex": 12, "columnIndex": 5}, "widthPixels": 480, "heightPixels": 300}}}}},
        # 자산_일별이력: 일별 추이 (유일)
        {"addChart": {"chart": {"spec": daily_growth_chart, "position": {"overlayPosition": {"anchorCell": {"sheetId": daily, "rowIndex": 3, "columnIndex": 6}, "widthPixels": 720, "heightPixels": 340}}}}},
        # 전용 시트 차트
        {"addChart": {"chart": {"spec": {"title": "세금우대 한도 사용률", "basicChart": {
            "chartType": "BAR", "legendPosition": "NO_LEGEND",
            "domains": [{"domain": {"sourceRange": sr(tax, 1, 5, 0, 1)}}],
            "series": [{"series": {"sourceRange": sr(tax, 1, 5, 4, 5)}, "targetAxis": "LEFT_AXIS"}],
            "headerCount": 1,
        }}, "position": {"overlayPosition": {"anchorCell": {"sheetId": tax, "rowIndex": 0, "columnIndex": 7}, "widthPixels": 400, "heightPixels": 260}}}}},
        {"addChart": {"chart": {"spec": {"title": "만기 D-day", "basicChart": {
            "chartType": "COLUMN", "legendPosition": "NO_LEGEND",
            "domains": [{"domain": {"sourceRange": sr(mat, 1, 10, 2, 3)}}],
            "series": [{"series": {"sourceRange": sr(mat, 1, 10, 4, 5)}, "targetAxis": "LEFT_AXIS"}],
            "headerCount": 1,
        }}, "position": {"overlayPosition": {"anchorCell": {"sheetId": mat, "rowIndex": 0, "columnIndex": 8}, "widthPixels": 360, "heightPixels": 260}}}}},
        {"addChart": {"chart": {"spec": {"title": "시나리오: 순자산 예측", "basicChart": {
            "chartType": "LINE", "legendPosition": "BOTTOM_LEGEND",
            "axis": [{"position": "BOTTOM_AXIS", "title": "개월"}, {"position": "LEFT_AXIS", "title": "원"}],
            "domains": [{"domain": {"sourceRange": sr(sc, 9, 70, 0, 1)}}],
            "series": [
                {"series": {"sourceRange": sr(sc, 9, 70, 1, 2)}, "targetAxis": "LEFT_AXIS"},
                {"series": {"sourceRange": sr(sc, 9, 70, 2, 3)}, "targetAxis": "LEFT_AXIS"},
            ],
            "headerCount": 1,
        }}, "position": {"overlayPosition": {"anchorCell": {"sheetId": sc, "rowIndex": 0, "columnIndex": 4}, "widthPixels": 480, "heightPixels": 300}}}}},
        {"addChart": {"chart": {"spec": {"title": "부채별 월상환", "basicChart": {
            "chartType": "COLUMN", "legendPosition": "NO_LEGEND",
            "domains": [{"domain": {"sourceRange": sr(ex["dsr"], 8, 18, 0, 1)}}],
            "series": [{"series": {"sourceRange": sr(ex["dsr"], 8, 18, 2, 3)}, "targetAxis": "LEFT_AXIS"}],
            "headerCount": 1,
        }}, "position": {"overlayPosition": {"anchorCell": {"sheetId": ex["dsr"], "rowIndex": 1, "columnIndex": 4}, "widthPixels": 400, "heightPixels": 280}}}}},
        {"addChart": {"chart": {"spec": {"title": "순자산 추세 (월)", "basicChart": {
            "chartType": "LINE", "legendPosition": "NO_LEGEND",
            "axis": [{"position": "BOTTOM_AXIS", "title": "연월"}, {"position": "LEFT_AXIS", "title": "원"}],
            "domains": [{"domain": {"sourceRange": sr(hist, 1, 100, 0, 1)}}],
            "series": [{"series": {"sourceRange": sr(hist, 1, 100, 3, 4)}, "targetAxis": "LEFT_AXIS"}],
            "headerCount": 1,
        }}, "position": {"overlayPosition": {"anchorCell": {"sheetId": hist, "rowIndex": 0, "columnIndex": 4}, "widthPixels": 480, "heightPixels": 280}}}}},
    ]
