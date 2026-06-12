/**
 * 월말 스냅샷 및 Google Docs 월간 리포트
 */

var ACCOUNT_TYPES = ['ISA', '주택청약', '연금저축', 'IRP', 'CMA', '보험', '현금', '적금', '주식', '부동산'];
var EXPENSE_CATEGORIES = ['식비', '교통', '쇼핑', '고정비', '의료', '여가', '대출상환', '대출이자', '기타'];

function takeMonthlySnapshot() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var monthly = ss.getSheetByName('월간집계');
  var history = ss.getSheetByName('순자산_이력');
  if (!monthly || !history) {
    showToast_('월간집계 또는 순자산_이력 시트가 없습니다.');
    return;
  }

  var year = monthly.getRange('B2').getValue();
  var month = monthly.getRange('B3').getValue();
  var yearMonth = year + '-' + (month < 10 ? '0' + month : month);

  var histData = history.getDataRange().getValues();
  for (var i = 1; i < histData.length; i++) {
    if (String(histData[i][0]) === yearMonth) {
      showToast_(yearMonth + ' 스냅샷이 이미 존재합니다.');
      return;
    }
  }

  var row = [yearMonth];
  row.push(monthly.getRange('B5').getValue()); // 총 자산
  row.push(monthly.getRange('B6').getValue()); // 총 부채
  row.push(monthly.getRange('B7').getValue()); // 순자산
  row.push(monthly.getRange('B8').getValue()); // P1 수입
  row.push(monthly.getRange('B9').getValue()); // P2 수입
  row.push(monthly.getRange('B11').getValue()); // 총 지출
  row.push(monthly.getRange('B12').getValue()); // 순저축

  for (var a = 0; a < ACCOUNT_TYPES.length; a++) {
    row.push(monthly.getRange(16 + a, 2).getValue());
  }

  history.appendRow(row);
  showToast_(yearMonth + ' 월말 스냅샷 저장 완료');
}

function generateMonthlyReport() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var settings = getSettings_();
  var monthly = ss.getSheetByName('월간집계');
  var dashboard = ss.getSheetByName('대시보드');

  if (!monthly) {
    showToast_('월간집계 시트를 찾을 수 없습니다.');
    return;
  }

  var year = monthly.getRange('B2').getValue();
  var month = monthly.getRange('B3').getValue();

  var totalAssets = Number(monthly.getRange('B5').getValue()) || 0;
  var totalDebt = Number(monthly.getRange('B6').getValue()) || 0;
  var netWorth = Number(monthly.getRange('B7').getValue()) || 0;
  var person1Income = Number(monthly.getRange('B8').getValue()) || 0;
  var person2Income = Number(monthly.getRange('B9').getValue()) || 0;
  var totalIncome = Number(monthly.getRange('B10').getValue()) || 0;
  var totalExpense = Number(monthly.getRange('B11').getValue()) || 0;
  var netSaving = Number(monthly.getRange('B12').getValue()) || 0;
  var savingRate = totalIncome > 0 ? netSaving / totalIncome : 0;

  var assetChange = '-';
  if (dashboard) {
    var changeVal = dashboard.getRange('B6').getValue();
    var changePct = dashboard.getRange('B7').getValue();
    if (changeVal !== '-' && changeVal !== '') {
      assetChange = formatKRW_(changeVal) + ' (' + formatPct_(changePct) + ')';
    }
  }

  var goalProgress = '-';
  var estimatedMonths = '-';
  if (dashboard) {
    goalProgress = formatPct_(dashboard.getRange('B18').getValue());
    var months = dashboard.getRange('B19').getValue();
    if (months !== '' && !isNaN(months)) {
      estimatedMonths = Math.round(months);
    }
  }

  var replacements = {
    '{{year}}': String(year),
    '{{month}}': String(month),
    '{{totalAssets}}': formatKRW_(totalAssets),
    '{{totalDebt}}': formatKRW_(totalDebt),
    '{{netWorth}}': formatKRW_(netWorth),
    '{{assetChange}}': assetChange,
    '{{totalIncome}}': formatKRW_(totalIncome),
    '{{person1Name}}': settings.person1Name,
    '{{person1Income}}': formatKRW_(person1Income),
    '{{person2Name}}': settings.person2Name,
    '{{person2Income}}': formatKRW_(person2Income),
    '{{totalExpense}}': formatKRW_(totalExpense),
    '{{netSaving}}': formatKRW_(netSaving),
    '{{savingRate}}': formatPct_(savingRate),
    '{{assetBreakdown}}': buildAssetBreakdown_(monthly),
    '{{expenseBreakdown}}': buildExpenseBreakdown_(ss, year, month),
    '{{goalAmount}}': formatKRW_(settings.goalAmount),
    '{{goalProgress}}': goalProgress,
    '{{estimatedMonths}}': String(estimatedMonths),
    '{{debtBreakdown}}': buildDebtBreakdown_(ss),
  };

  var docId = createReportDoc_(settings, year, month, replacements);
  showToast_('월간 리포트 생성: ' + year + '년 ' + month + '월');
  Logger.log('Report doc: https://docs.google.com/document/d/' + docId);
}

function buildAssetBreakdown_(monthly) {
  var lines = [];
  for (var i = 0; i < ACCOUNT_TYPES.length; i++) {
    var val = Number(monthly.getRange(16 + i, 2).getValue()) || 0;
    if (val > 0) {
      lines.push('· ' + ACCOUNT_TYPES[i] + ': ' + formatKRW_(val));
    }
  }
  return lines.length ? lines.join('\n') : '· (데이터 없음)';
}

function buildDebtBreakdown_(ss) {
  var sheet = ss.getSheetByName('부채');
  if (!sheet) return '· (데이터 없음)';
  var data = sheet.getDataRange().getValues();
  var lines = [];
  for (var i = 1; i < data.length; i++) {
    var bal = Number(data[i][3]) || 0;
    if (bal > 0) {
      lines.push('· ' + data[i][1] + ': ' + formatKRW_(bal));
    }
  }
  return lines.length ? lines.join('\n') : '· (부채 없음)';
}

function buildExpenseBreakdown_(ss, year, month) {
  var expenseSheet = ss.getSheetByName('지출');
  if (!expenseSheet) return '· (데이터 없음)';

  var start = new Date(year, month - 1, 1);
  var end = new Date(year, month, 0);
  var data = expenseSheet.getDataRange().getValues();
  var totals = {};

  for (var c = 0; c < EXPENSE_CATEGORIES.length; c++) {
    totals[EXPENSE_CATEGORIES[c]] = 0;
  }

  for (var i = 1; i < data.length; i++) {
    var d = data[i][0];
    if (!(d instanceof Date)) continue;
    if (d < start || d > end) continue;
    var cat = String(data[i][1] || '기타');
    var amt = Number(data[i][2]) || 0;
    totals[cat] = (totals[cat] || 0) + amt;
  }

  var lines = [];
  for (var key in totals) {
    if (totals[key] > 0) {
      lines.push('· ' + key + ': ' + formatKRW_(totals[key]));
    }
  }
  return lines.length ? lines.join('\n') : '· (데이터 없음)';
}

function createReportDoc_(settings, year, month, replacements) {
  var title = year + '년 ' + month + '월 가계·투자 월간 리포트';
  var docId;

  if (settings.docsTemplateId) {
    try {
      var file = DriveApp.getFileById(settings.docsTemplateId).makeCopy(title);
      if (settings.driveFolderId) {
        DriveApp.getFolderById(settings.driveFolderId).addFile(file);
        DriveApp.getRootFolder().removeFile(file);
      }
      docId = file.getId();
    } catch (e) {
      Logger.log('템플릿 복사 실패, 새 문서 생성: ' + e.message);
      docId = DocumentApp.create(title).getId();
    }
  } else {
    docId = DocumentApp.create(title).getId();
  }

  var doc = DocumentApp.openById(docId);
  var body = doc.getBody();

  for (var key in replacements) {
    var pattern = key.replace(/\{/g, '\\{').replace(/\}/g, '\\}');
    body.replaceText(pattern, String(replacements[key]));
  }

  doc.saveAndClose();
  return docId;
}
