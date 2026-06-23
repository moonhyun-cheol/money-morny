"""인생라인 시트 — life_plan / life_timeline → Google Sheets."""

from __future__ import annotations

from typing import Any, Callable

LIFE_SHEET_IDS = {
    "life_line": 19,
    "life_phase": 20,
    "quarterly": 21,
}

try:
    from config.life_plan import LIFE_PHASE_RANGES, LIFE_PHASES, MONTHLY_INVEST_TOTAL
    from config.life_timeline import QUARTERLY_MILESTONES, build_yearly_timeline
except ImportError:
    LIFE_PHASE_RANGES = []
    LIFE_PHASES = []
    MONTHLY_INVEST_TOTAL = 2_078_032
    QUARTERLY_MILESTONES = []
    build_yearly_timeline = lambda: []  # noqa: E731


def life_sheet_defs() -> list[tuple[str, int]]:
    return [
        ("인생라인", LIFE_SHEET_IDS["life_line"]),
        ("라이프페이즈", LIFE_SHEET_IDS["life_phase"]),
        ("분기체크", LIFE_SHEET_IDS["quarterly"]),
    ]


def build_life_line_requests(
    _cell: Callable,
    _row_data: Callable,
    COLORS: dict,
) -> list[dict]:
    ex = LIFE_SHEET_IDS
    reqs: list[dict] = []

    # ── 라이프페이즈 (한눈에보기 TODAY() 조회) ──
    phase_headers = ["단계", "이름", "시작일", "종료일", "허리띠", "월 여유(원)", "이번 달 할 일"]
    phase_rows = [_row_data([_cell(0, j, v) for j, v in enumerate(phase_headers)])]
    for i, row in enumerate(LIFE_PHASE_RANGES, start=2):
        phase_rows.append(
            _row_data([_cell(i - 1, j, v) for j, v in enumerate(row)])
        )
    reqs.append({
        "updateCells": {
            "range": {"sheetId": ex["life_phase"], "startRowIndex": 0, "startColumnIndex": 0},
            "rows": phase_rows,
            "fields": "userEnteredValue",
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": ex["life_phase"], "startRowIndex": 1, "endRowIndex": 1 + len(LIFE_PHASE_RANGES)},
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"},
                }
            },
            "fields": "userEnteredFormat.numberFormat",
        }
    })
    for col in (2, 3):
        reqs.append({
            "repeatCell": {
                "range": {
                    "sheetId": ex["life_phase"],
                    "startRowIndex": 1,
                    "endRowIndex": 1 + len(LIFE_PHASE_RANGES),
                    "startColumnIndex": col,
                    "endColumnIndex": col + 1,
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"},
                    }
                },
                "fields": "userEnteredFormat.numberFormat",
            }
        })
    reqs.append({
        "repeatCell": {
            "range": {
                "sheetId": ex["life_phase"],
                "startRowIndex": 1,
                "endRowIndex": 1 + len(LIFE_PHASE_RANGES),
                "startColumnIndex": 5,
                "endColumnIndex": 6,
            },
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
            "fields": "userEnteredFormat.numberFormat",
        }
    })

    # 페이즈 요약 (LIFE_PHASES — belt·기간 텍스트)
    summary_start = 2 + len(LIFE_PHASE_RANGES)
    summary_rows = [
        _row_data([_cell(summary_start - 1, 0, "페이즈 요약 (상세)")]),
        _row_data([_cell(summary_start, j, v) for j, v in enumerate(["ID", "이름", "기간", "허리띠", "요약", "할 일"])]),
    ]
    for i, ph in enumerate(LIFE_PHASES, summary_start + 2):
        summary_rows.append(_row_data([
            _cell(i - 1, 0, ph["id"]),
            _cell(i - 1, 1, ph["name"]),
            _cell(i - 1, 2, ph["period"]),
            _cell(i - 1, 3, ph["belt_label"]),
            _cell(i - 1, 4, ph["summary"]),
            _cell(i - 1, 5, ph["tasks"]),
        ]))
    reqs.append({
        "updateCells": {
            "range": {"sheetId": ex["life_phase"], "startRowIndex": summary_start - 1, "startColumnIndex": 0},
            "rows": summary_rows,
            "fields": "userEnteredValue",
        }
    })

    # ── 인생라인 (연도별 투영) ──
    line_headers = [
        "연도", "나이", "페이즈", "허리", "단계", "월 세후", "월 저축+여유", "월 여유",
        "유동자산", "집 지분", "대출", "순자산", "주거", "가족", "주요 이벤트",
    ]
    line_rows = [
        _row_data([_cell(0, 0, "연도별 인생라인 (config/life_timeline.py)")]),
        _row_data([_cell(0, j, v) for j, v in enumerate(line_headers)]),
    ]
    for i, row in enumerate(build_yearly_timeline(), start=3):
        line_rows.append(_row_data([
            _cell(i - 1, 0, row["year"]),
            _cell(i - 1, 1, f"만 {row['age']}세"),
            _cell(i - 1, 2, row["phase_id"]),
            _cell(i - 1, 3, row["belt"]),
            _cell(i - 1, 4, row["phase_name"]),
            _cell(i - 1, 5, row["monthly_net"]),
            _cell(i - 1, 6, row["monthly_save"]),
            _cell(i - 1, 7, row["monthly_free"]),
            _cell(i - 1, 8, row["liquid_assets"]),
            _cell(i - 1, 9, row["home_equity"]),
            _cell(i - 1, 10, row["mortgage"]),
            _cell(i - 1, 11, row["net_worth"]),
            _cell(i - 1, 12, row["housing"]),
            _cell(i - 1, 13, row["family"]),
            _cell(i - 1, 14, row["events"]),
        ]))
    reqs.append({
        "updateCells": {
            "range": {"sheetId": ex["life_line"], "startRowIndex": 0, "startColumnIndex": 0},
            "rows": line_rows,
            "fields": "userEnteredValue",
        }
    })
    reqs.append({
        "updateSheetProperties": {
            "properties": {"sheetId": ex["life_line"], "gridProperties": {"frozenRowCount": 2}},
            "fields": "gridProperties.frozenRowCount",
        }
    })
    for col_start, col_end in [(5, 12)]:
        reqs.append({
            "repeatCell": {
                "range": {
                    "sheetId": ex["life_line"],
                    "startRowIndex": 2,
                    "endRowIndex": 2 + 20,
                    "startColumnIndex": col_start,
                    "endColumnIndex": col_end,
                },
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
                "fields": "userEnteredFormat.numberFormat",
            }
        })

    # ── 분기체크 ──
    q_headers = ["분기", "영역", "할 일", "메모", "완료"]
    q_rows = [
        _row_data([_cell(0, 0, "분기별 마일스톤 — 체크 후 E열에 O")]),
        _row_data([_cell(0, j, v) for j, v in enumerate(q_headers)]),
    ]
    for i, (q, area, task, memo) in enumerate(QUARTERLY_MILESTONES, start=3):
        q_rows.append(_row_data([
            _cell(i - 1, 0, q),
            _cell(i - 1, 1, area),
            _cell(i - 1, 2, task),
            _cell(i - 1, 3, memo),
            _cell(i - 1, 4, ""),
        ]))
    reqs.append({
        "updateCells": {
            "range": {"sheetId": ex["quarterly"], "startRowIndex": 0, "startColumnIndex": 0},
            "rows": q_rows,
            "fields": "userEnteredValue",
        }
    })

    # 헤더 서식
    for sheet_id in ex.values():
        reqs.append({
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
        })
    for sheet_id, color in [
        (ex["life_line"], {"red": 0.55, "green": 0.35, "blue": 0.75}),
        (ex["life_phase"], {"red": 0.85, "green": 0.45, "blue": 0.55}),
        (ex["quarterly"], {"red": 0.45, "green": 0.65, "blue": 0.55}),
    ]:
        reqs.append({
            "updateSheetProperties": {
                "properties": {"sheetId": sheet_id, "tabColor": color},
                "fields": "tabColor",
            }
        })

    return reqs


def life_phase_lookup_formulas() -> dict[str, str]:
    """한눈에보기 — 라이프페이즈 시트 기준 수식."""
    m = "MATCH(TODAY(),'라이프페이즈'!C:C,1)"
    return {
        "phase_id": f"=INDEX('라이프페이즈'!A:A,{m})",
        "phase_name": f"=INDEX('라이프페이즈'!B:B,{m})",
        "belt": f"=INDEX('라이프페이즈'!E:E,{m})",
        "target_free": f"=INDEX('라이프페이즈'!F:F,{m})",
        "tasks": f"=INDEX('라이프페이즈'!G:G,{m})",
        "target_save": f"={MONTHLY_INVEST_TOTAL}",
    }
