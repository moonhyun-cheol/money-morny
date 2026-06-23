"""KB국민은행 거래내역 PDF 파싱 (암호 = 생년월일 6자리)."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

from analyze_fixed_costs import Transaction, _parse_amount, _parse_date

# 거래일시, 적요, 보낸분/받는분, 출금액, 입금액, 잔액 ...
DATE_AT_LINE = re.compile(
    r"(\d{4}[.\-/]\d{2}[.\-/]\d{2}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)"
)
AMOUNT_TOKEN = re.compile(r"[\d,]+")


def _extract_pdf_text(path: Path, password: str | None) -> str:
    try:
        import pdfplumber
    except ImportError as e:
        raise ImportError("pdfplumber 필요: pip install pdfplumber") from e

    parts: list[str] = []
    with pdfplumber.open(str(path), password=password or "") as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for table in tables:
                for row in table:
                    if row:
                        parts.append("\t".join(str(c or "").strip() for c in row))
            text = page.extract_text() or ""
            if text:
                parts.append(text)
    return "\n".join(parts)


def _row_to_tx(cells: list[str], source: str) -> Transaction | None:
    if not cells:
        return None
    joined = " ".join(cells)
    dt = None
    for c in cells:
        dt = _parse_date(c)
        if dt:
            break
    if dt is None:
        m = DATE_AT_LINE.search(joined)
        if m:
            dt = _parse_date(m.group(1))
    if dt is None:
        return None

    amounts: list[int] = []
    for c in cells:
        s = str(c or "").strip()
        if re.fullmatch(r"[\d,]+", s.replace(" ", "")):
            a = _parse_amount(s)
            if a and a > 0:
                amounts.append(a)

    # 표 형식: ... 적요 ... 출금 입금 잔액
    withdraw = None
    merchant_parts: list[str] = []
    for c in cells:
        s = str(c or "").strip()
        if not s or s in ("-", "0", "출금액", "입금액", "잔액", "거래일시", "적요"):
            continue
        if DATE_AT_LINE.match(s) or _parse_date(s):
            continue
        if re.fullmatch(r"[\d,]+", s.replace(" ", "")):
            continue
        merchant_parts.append(s)

    # 출금·입금·잔액 순서 가정
    if len(amounts) >= 3:
        w, dep, _bal = amounts[0], amounts[1], amounts[2]
        if w > 0:
            withdraw = w
        elif dep > 0:
            return None  # 입금만 — 지출 분석 제외
    elif len(amounts) == 2:
        if amounts[0] > 0 and amounts[1] > amounts[0] * 5:
            withdraw = amounts[0]
    elif len(amounts) == 1:
        withdraw = amounts[0]

    if not withdraw or withdraw <= 0:
        return None

    merchant = " ".join(merchant_parts).strip() or joined[:80]
    return Transaction(dt=dt, amount=withdraw, merchant=merchant, source=source)


def _parse_text_line(line: str, source: str) -> Transaction | None:
    line = line.strip()
    if not line or "거래일시" in line or "합계" in line or "총 출금" in line:
        return None
    m = DATE_AT_LINE.search(line)
    if not m:
        return None
    dt = _parse_date(m.group(1))
    if dt is None:
        return None

    tail = line[m.end() :].strip()
    nums = AMOUNT_TOKEN.findall(tail)
    amounts = [_parse_amount(n) for n in nums]
    amounts = [a for a in amounts if a and a > 0]
    if not amounts:
        return None

    withdraw = amounts[0]
    if len(amounts) >= 3 and amounts[1] == 0:
        withdraw = amounts[0]
    elif len(amounts) >= 2 and amounts[0] < amounts[-1]:
        withdraw = amounts[0]

    desc = DATE_AT_LINE.sub("", line)
    for n in nums:
        desc = desc.replace(n, " ")
    merchant = re.sub(r"\s+", " ", desc).strip()[:120]
    if withdraw <= 0:
        return None
    return Transaction(dt=dt, amount=withdraw, merchant=merchant, source=source)


def read_kb_pdf(path: Path, password: str | None = None) -> list[Transaction]:
    raw = _extract_pdf_text(path, password)
    if not raw.strip():
        raise ValueError("PDF에서 텍스트를 읽지 못했습니다 (암호 확인)")

    txs: list[Transaction] = []
    seen: set[tuple] = set()

    for line in raw.splitlines():
        if "\t" in line:
            cells = [c.strip() for c in line.split("\t")]
            tx = _row_to_tx(cells, path.name)
        else:
            tx = _parse_text_line(line, path.name)
        if tx is None:
            continue
        key = (tx.dt, tx.amount, tx.merchant[:40])
        if key in seen:
            continue
        seen.add(key)
        txs.append(tx)

    if not txs:
        raise ValueError(
            "거래를 파싱하지 못했습니다. PDF가 스캔본이면 CSV/Excel 내보내기를 이용하세요."
        )
    return sorted(txs, key=lambda t: (t.dt, t.amount))
