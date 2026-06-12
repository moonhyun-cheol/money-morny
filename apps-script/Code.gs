/**
 * 재무관리 — 메인 진입점 및 유틸
 */

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('재무관리')
    .addSubMenu(
      ui.createMenu('📊 갱신')
        .addItem('시세+환율+일별자산', 'refreshAllMarketData')
        .addItem('시세만', 'refreshStockPrices')
        .addItem('환율만', 'refreshFxRates')
        .addItem('일별 자산 스냅샷', 'takeDailyAssetSnapshot')
    )
    .addSubMenu(
      ui.createMenu('💸 자산 이동')
        .addItem('템플릿 적용', 'applyTransferTemplate')
        .addItem('예정 전체 실행', 'executePendingTransfers')
        .addItem('행 지정 실행', 'executeSelectedTransfer')
    )
    .addSubMenu(
      ui.createMenu('📅 리포트·알림')
        .addItem('만기 임박 알림', 'showMaturityAlerts')
        .addItem('월말 스냅샷', 'takeMonthlySnapshot')
        .addItem('월간 리포트 생성', 'generateMonthlyReport')
    )
    .addSeparator()
    .addItem('⚙ 트리거 설치 (자동)', 'installTriggers')
    .addItem('트리거 제거', 'removeTriggers')
    .addToUi();
}

function getSettings_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('설정');
  return {
    person1Name: sheet.getRange('B2').getValue() || 'Person1',
    person2Name: sheet.getRange('B3').getValue() || 'Person2',
    goalAmount: Number(sheet.getRange('B4').getValue()) || 0,
    trendMonths: Number(sheet.getRange('B6').getValue()) || 6,
    docsTemplateId: String(sheet.getRange('B7').getValue() || ''),
    driveFolderId: String(sheet.getRange('B8').getValue() || ''),
  };
}

function formatKRW_(n) {
  if (n === '' || n === null || isNaN(n)) return '-';
  return '₩' + Math.round(n).toLocaleString('ko-KR');
}

function formatPct_(n) {
  if (n === '' || n === null || isNaN(n)) return '-';
  return (n * 100).toFixed(1) + '%';
}

function showToast_(msg) {
  SpreadsheetApp.getActiveSpreadsheet().toast(msg, '재무관리', 5);
}

function checkEndOfMonthAndRun_() {
  var today = new Date();
  var tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);
  if (tomorrow.getDate() === 1) {
    takeMonthlySnapshot();
    generateMonthlyReport();
  }
}

function checkDailyAlerts_() {
  checkMaturityAlertsSilent_();
}

function checkMaturityAlertsSilent_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('만기_캘린더');
  if (!sheet) return;
  var data = sheet.getDataRange().getValues();
  var n = 0;
  for (var i = 1; i < data.length; i++) {
    var dday = data[i][4];
    if (typeof dday === 'number' && dday >= 0 && dday <= 7) n++;
  }
  if (n > 0) {
    showToast_('만기 7일 이내 ' + n + '건 — 만기_캘린더 확인');
  }
}
