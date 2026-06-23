#!/usr/bin/env python3
"""KB PDF — 결제일·간격 패턴 분석 (정기 소액)."""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from kb_pdf_parser import read_kb_pdf


def day_of_month(d: date) -> int:
    return d.day


def analyze_recurring(txs, *, min_count: int = 2, max_amount: int = 100_000) -> None:
    """같은 금액 + 비슷한 일(±2) 또는 고정 간격(28~31일)."""
    outflows = [t for t in txs if t.amount <= max_amount]

    by_amount: dict[int, list] = defaultdict(list)
    for t in outflows:
        by_amount[t.amount].append(t)

    print("=" * 72)
    print("정기 소액 후보 (같은 금액 2회+, 10만 이하)")
    print("=" * 72)

    for amount in sorted(by_amount.keys(), reverse=True):
        group = by_amount[amount]
        if len(group) < min_count:
            continue
        days = sorted({t.dt for t in group})
        doms = [d.day for d in days]
        # same day of month cluster
        dom_counts: dict[int, int] = defaultdict(int)
        for d in days:
            dom_counts[d.day] += 1
        top_dom = max(dom_counts.items(), key=lambda x: x[1])
        intervals = [(days[i + 1] - days[i]).days for i in range(len(days) - 1)]
        avg_iv = sum(intervals) / len(intervals) if intervals else 0
        monthly_like = 27 <= avg_iv <= 32 if intervals else False
        same_dom = top_dom[1] >= 2 and top_dom[0]

        merchants = list({t.merchant[:40] for t in group})[:3]
        flag = []
        if same_dom:
            flag.append(f"매월 ~{top_dom[0]}일")
        if monthly_like:
            flag.append(f"간격 ~{avg_iv:.0f}일")
        if not flag:
            continue

        print(f"\n{amount:>8,}원 × {len(group)}회  [{', '.join(flag)}]")
        for t in sorted(group, key=lambda x: x.dt)[-6:]:
            print(f"  {t.dt}  {t.merchant[:55]}")
        if merchants:
            print(f"  적요: {merchants[0]}")

    # by day-of-month clusters (any amount, small)
    print("\n" + "=" * 72)
    print("결제일 고정 (매월 같은 날 ±1, 2회+, 1~10만)")
    print("=" * 72)
    by_dom: dict[int, list] = defaultdict(list)
    for t in outflows:
        if t.amount > 100_000:
            continue
        by_dom[t.dt.day].append(t)

    for dom in sorted(by_dom.keys()):
        g = by_dom[dom]
        if len(g) < 2:
            continue
        months = len({(t.dt.year, t.dt.month) for t in g})
        if months < 2:
            continue
        amt_counts: dict[int, int] = defaultdict(int)
        for t in g:
            amt_counts[t.amount] += 1
        common = sorted(amt_counts.items(), key=lambda x: -x[1])[:3]
        samples = [f"{a:,}({c}회)" for a, c in common]
        m0 = g[0].merchant[:35]
        print(f"  매월 {dom:2d}일 전후: {samples}  예) {m0}")


def main() -> None:
    pdf = next(ROOT.glob("KB*.pdf"))
    txs = read_kb_pdf(pdf, "991216")
    print(f"기간: {min(t.dt for t in txs)} ~ {max(t.dt for t in txs)}  출금 {len(txs)}건\n")
    analyze_recurring(txs)


if __name__ == "__main__":
    main()
