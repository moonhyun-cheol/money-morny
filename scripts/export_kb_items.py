#!/usr/bin/env python3
"""KB PDF → 항목명·금액 목록 (고정비 후보)."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from analyze_fixed_costs import find_fixed_candidates, write_report
from kb_pdf_parser import read_kb_pdf

OUT_TXT = ROOT / "sheets" / "KB고정비후보.txt"
OUT_XLSX = ROOT / "sheets" / "고정비분석.xlsx"


def main() -> None:
    pdf = next(ROOT.glob("KB*.pdf"))
    txs = read_kb_pdf(pdf, "991216")
    cands = find_fixed_candidates(txs, min_count=2, min_months=2, min_amount=1_000)
    cands = sorted(cands, key=lambda c: (-c.amount, -c.count))

    lines = [
        f"KB 거래내역 고정비 후보 (같은 금액 2회+, 2개월+)",
        f"기간: {min(t.dt for t in txs)} ~ {max(t.dt for t in txs)} | 출금 {len(txs)}건",
        "",
        f"{'금액':>12}  {'횟수':>4}  {'월':>3}  항목명",
        "-" * 80,
    ]
    for c in cands:
        names = [m for m, _ in c.merchants[:5]]
        label = " / ".join(names) if names else "(적요 없음)"
        lines.append(f"{c.amount:>12,}  {c.count:>4}  {c.month_count:>3}  {label}")

    lines += [
        "",
        "※ 항목명은 PDF 추출 그대로입니다. 본인 계좌 이체·입금은 고정비에서 제외하세요.",
    ]
    text = "\n".join(lines)
    OUT_TXT.parent.mkdir(parents=True, exist_ok=True)
    OUT_TXT.write_text(text, encoding="utf-8")
    write_report(txs, cands, OUT_XLSX)
    print(text)
    print(f"\n저장: {OUT_TXT}")
    print(f"저장: {OUT_XLSX}")


if __name__ == "__main__":
    main()
