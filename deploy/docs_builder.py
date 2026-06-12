"""Google Docs 월간 리포트 템플릿 생성."""

from __future__ import annotations


def create_report_template(docs_service) -> str:
    """월간 리포트 Docs 템플릿 생성. documentId 반환."""
    doc = docs_service.documents().create(body={"title": "월간리포트_템플릿"}).execute()
    document_id = doc["documentId"]

    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": (
                    "{{year}}년 {{month}}월 가계·투자 월간 리포트\n\n"
                    "■ 요약\n"
                    "· 총 자산: {{totalAssets}}\n"
                    "· 총 부채: {{totalDebt}}\n"
                    "· 순자산: {{netWorth}} (전월 대비 {{assetChange}})\n"
                    "· 이번 달 수입: {{totalIncome}} ({{person1Name}} {{person1Income}} / {{person2Name}} {{person2Income}})\n"
                    "· 이번 달 지출: {{totalExpense}}\n"
                    "· 순저축: {{netSaving}} (저축률 {{savingRate}})\n\n"
                    "■ 자산 구성\n"
                    "{{assetBreakdown}}\n\n"
                    "■ 부채 현황\n"
                    "{{debtBreakdown}}\n\n"
                    "■ 지출 분석 (카테고리별)\n"
                    "{{expenseBreakdown}}\n\n"
                    "■ 목표 진행\n"
                    "· 목표 {{goalAmount}} 대비 {{goalProgress}} 달성\n"
                    "· 현재 추세: 약 {{estimatedMonths}}개월 후 달성 예상\n\n"
                    "■ 메모\n"
                    "\n\n"
                ),
            }
        }
    ]

    docs_service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()
    return document_id
