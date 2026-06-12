/**
 * FxRates.gs
 * 이동 템플릿 → 자산_이동 시트에 적용
 */

function applyTransferTemplate() {
  var ui = SpreadsheetApp.getUi();
  var res = ui.prompt(
    '이동 템플릿 적용',
    '이동_템플릿 시트의 행 번호(2부터)와 금액을 입력하세요.\n형식: 행번호,금액  (예: 2,20000000)',
    ui.ButtonSet.OK_CANCEL
  );
  if (res.getSelectedButton() !== ui.Button.OK) return;

  var parts = res.getResponseText().split(',');
  if (parts.length < 2) {
    showToast_('형식: 행번호,금액');
    return;
  }

  var tplRow = parseInt(parts[0].trim(), 10);
  var amount = Number(parts[1].trim().replace(/,/g, ''));
  if (isNaN(tplRow) || tplRow < 2 || isNaN(amount)) {
    showToast_('행번호와 금액을 확인하세요.');
    return;
  }

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var tpl = ss.getSheetByName('이동_템플릿');
  var dest = ss.getSheetByName('자산_이동');
  if (!tpl || !dest) {
    showToast_('시트를 찾을 수 없습니다.');
    return;
  }

  var t = tpl.getRange(tplRow, 1, 1, 7).getValues()[0];
  dest.appendRow([
    new Date(),
    t[1], t[2], t[3], t[4], t[5],
    amount,
    '', '', '',
    t[6] || '',
    '예정',
  ]);

  showToast_('템플릿 「' + t[0] + '」→ 자산_이동에 추가 (금액 ' + amount.toLocaleString() + '원)');
}

function showMaturityAlerts() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('만기_캘린더');
  if (!sheet) return;

  var data = sheet.getDataRange().getValues();
  var alerts = [];
  for (var i = 1; i < data.length; i++) {
    var dday = data[i][4];
    if (typeof dday === 'number' && dday >= 0 && dday <= 30) {
      alerts.push(data[i][2] + ' (' + Math.round(dday) + '일 후)');
    }
  }

  if (alerts.length) {
    SpreadsheetApp.getUi().alert('만기 임박 (30일 이내)', alerts.join('\n'), SpreadsheetApp.getUi().ButtonSet.OK);
  } else {
    showToast_('30일 이내 만기 없음');
  }
}
