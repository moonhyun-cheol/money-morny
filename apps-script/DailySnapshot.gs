/**
 * 담당자별·합계 일별 자산 스냅샷
 * 오늘 날짜 행이 있으면 덮어쓰기 → 항상 최신 평가 반영
 */

function takeDailyAssetSnapshot() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var history = ss.getSheetByName('자산_일별이력');
  var assets = ss.getSheetByName('자산_종목');
  if (!history || !assets) {
    showToast_('자산_일별이력 또는 자산_종목 시트가 없습니다.');
    return;
  }

  var settings = getSettings_();
  var totals = sumAssetsByPerson_(assets, settings.person1Name, settings.person2Name);

  var today = new Date();
  today.setHours(0, 0, 0, 0);

  var rowIdx = findDateRow_(history, today);
  var row = [today, totals.p1, totals.p2, totals.joint, totals.total];

  if (rowIdx > 0) {
    history.getRange(rowIdx, 1, rowIdx, 5).setValues([row]);
  } else {
    history.appendRow(row);
  }
}

function sumAssetsByPerson_(assetsSheet, p1Name, p2Name) {
  var lastRow = assetsSheet.getLastRow();
  if (lastRow < 2) {
    return { p1: 0, p2: 0, joint: 0, total: 0 };
  }

  var colCount = Math.max(14, assetsSheet.getLastColumn());
  var data = assetsSheet.getRange(2, 1, lastRow, colCount).getValues();

  var p1 = 0;
  var p2 = 0;
  var joint = 0;

  for (var i = 0; i < data.length; i++) {
    var val = rowAssetValue_(data[i]);
    if (val <= 0) continue;

    var person = String(data[i][2] || '').trim();
    if (person === p1Name) {
      p1 += val;
    } else if (person === p2Name) {
      p2 += val;
    } else if (person === '공동') {
      joint += val;
    }
  }

  return {
    p1: p1,
    p2: p2,
    joint: joint,
    total: p1 + p2 + joint,
  };
}

function rowAssetValue_(row) {
  var evalAmt = Number(row[8]);
  if (!isNaN(evalAmt) && evalAmt > 0) return evalAmt;

  var qty = Number(row[5]) || 0;
  var price = Number(row[7]) || 0;
  var fx = Number(row[13]) || 1;
  return qty * price * fx;
}

function findDateRow_(sheet, targetDate) {
  var lastRow = sheet.getLastRow();
  if (lastRow < 4) return -1;

  var dates = sheet.getRange(4, 1, lastRow, 1).getValues();
  for (var i = 0; i < dates.length; i++) {
    var d = dates[i][0];
    if (d instanceof Date && sameDay_(d, targetDate)) {
      return i + 4;
    }
    if (typeof d === 'string' && d) {
      var parsed = new Date(d);
      if (!isNaN(parsed.getTime()) && sameDay_(parsed, targetDate)) {
        return i + 4;
      }
    }
  }
  return -1;
}

function sameDay_(a, b) {
  return a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate();
}
