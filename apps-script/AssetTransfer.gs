/**
 * 자산 간 이동 — 자산_종목 열: A유형 B계좌명 C담당자 D티커 E종목명 F수량 G평단 H현재가 I평가(원)
 */

var TRANSFER_TYPES_EXEC = {
  '계좌간이동': 'transfer',
  'ISA만기→연금': 'transfer',
  '투자금인출': 'transfer',
  '종목전환': 'transfer',
  '전량현금화': 'liquidate',
  '아파트구매': 'apartment',
  '부채발생': 'debtIncur',
  '부채상환': 'debtRepay',
};

function executePendingTransfers() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('자산_이동');
  if (!sheet) {
    showToast_('자산_이동 시트가 없습니다.');
    return;
  }

  var lastRow = sheet.getLastRow();
  var done = 0;
  var errors = [];

  for (var r = 2; r <= lastRow; r++) {
    var status = String(sheet.getRange(r, 12).getValue() || '').trim();
    if (status !== '예정') continue;

    var result = executeTransferRow_(ss, sheet, r);
    if (result.ok) {
      sheet.getRange(r, 12).setValue('완료');
      done++;
    } else {
      errors.push('행' + r + ': ' + result.msg);
    }
  }

  var msg = done + '건 이동 완료';
  if (errors.length) msg += ' / 실패 ' + errors.length + '건';
  showToast_(msg);
  if (errors.length) Logger.log(errors.join('\n'));
}

function executeSelectedTransfer() {
  var ui = SpreadsheetApp.getUi();
  var res = ui.prompt('자산 이동 실행', '실행할 행 번호를 입력하세요 (자산_이동 시트):', ui.ButtonSet.OK_CANCEL);
  if (res.getSelectedButton() !== ui.Button.OK) return;

  var row = parseInt(res.getResponseText(), 10);
  if (isNaN(row) || row < 2) {
    showToast_('올바른 행 번호를 입력하세요.');
    return;
  }

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('자산_이동');
  var result = executeTransferRow_(ss, sheet, row);
  if (result.ok) {
    sheet.getRange(row, 12).setValue('완료');
    showToast_('행 ' + row + ' 이동 완료');
  } else {
    showToast_('실패: ' + result.msg);
  }
}

function executeTransferRow_(ss, sheet, row) {
  var type = String(sheet.getRange(row, 2).getValue() || '').trim();
  var fromType = String(sheet.getRange(row, 3).getValue() || '').trim();
  var fromName = String(sheet.getRange(row, 4).getValue() || '').trim();
  var toType = String(sheet.getRange(row, 5).getValue() || '').trim();
  var toName = String(sheet.getRange(row, 6).getValue() || '').trim();
  var amount = Number(sheet.getRange(row, 7).getValue());
  var fromStock = String(sheet.getRange(row, 8).getValue() || '').trim();
  var toStock = String(sheet.getRange(row, 9).getValue() || '').trim();
  var debtName = String(sheet.getRange(row, 10).getValue() || '').trim();

  if (!amount || amount <= 0) return { ok: false, msg: '금액을 확인하세요.' };

  var mode = TRANSFER_TYPES_EXEC[type] || 'transfer';

  try {
    if (mode === 'liquidate') {
      return executeLiquidation_(ss, fromType, fromName, toType, toName, amount);
    }
    if (mode === 'apartment') {
      return executeApartmentPurchase_(ss, fromType, fromName, toType, toName, amount, toStock || toName, debtName);
    }
    if (mode === 'debtRepay') {
      return executeDebtRepayment_(ss, fromType, fromName, debtName, amount);
    }
    if (mode === 'debtIncur') {
      return executeDebtIncurrence_(ss, toType, toName, debtName, amount, type);
    }
    return executeAccountTransfer_(ss, fromType, fromName, toType, toName, amount, fromStock, toStock);
  } catch (e) {
    return { ok: false, msg: e.message };
  }
}

function executeAccountTransfer_(ss, fromType, fromName, toType, toName, amount, fromStock, toStock) {
  if (!fromType || !fromName || !toType || !toName) {
    return { ok: false, msg: '출발/도착 계좌를 입력하세요.' };
  }

  var withdrawn = withdrawFromAccount_(ss, fromType, fromName, amount, fromStock);
  if (!withdrawn.ok) return withdrawn;

  depositToAccount_(ss, toType, toName, amount, toStock);
  return { ok: true, msg: '' };
}

function executeLiquidation_(ss, fromType, fromName, toType, toName, amount) {
  if (!fromType || !fromName) return { ok: false, msg: '출발 계좌를 입력하세요.' };
  if (!toType || !toName) {
    toType = '현금';
    toName = '전량현금화';
  }

  var total = getAccountTotal_(ss, fromType, fromName);
  if (total <= 0) return { ok: false, msg: '출발 계좌에 자산이 없습니다.' };

  var moveAmount = amount > 0 ? Math.min(amount, total) : total;
  zeroOutAccount_(ss, fromType, fromName);
  depositToAccount_(ss, toType, toName, moveAmount, '');
  return { ok: true, msg: '' };
}

function executeApartmentPurchase_(ss, fromType, fromName, toType, toName, downPayment, propertyName, debtName) {
  if (!propertyName) propertyName = toName || '부동산';
  if (!toType) toType = '부동산';

  if (fromType && fromName && downPayment > 0) {
    var w = withdrawFromAccount_(ss, fromType, fromName, downPayment, '');
    if (!w.ok) return w;
  }

  appendAssetRow_(ss, toType, toName || propertyName, propertyName, downPayment);

  if (debtName) {
    var debtSheet = ss.getSheetByName('부채');
    if (debtSheet) {
      var found = findDebtRow_(debtSheet, debtName);
      if (found < 0) {
        showToast_('부채 시트에 「' + debtName + '」를 등록해 주세요.');
      }
    }
  }

  return { ok: true, msg: '' };
}

function executeDebtRepayment_(ss, cashType, cashName, debtName, amount) {
  if (!debtName) return { ok: false, msg: '부채명을 입력하세요.' };

  var debtSheet = ss.getSheetByName('부채');
  var row = findDebtRow_(debtSheet, debtName);
  if (row < 0) return { ok: false, msg: '부채를 찾을 수 없습니다: ' + debtName };

  var balance = Number(debtSheet.getRange(row, 4).getValue());
  if (balance < amount) return { ok: false, msg: '상환액이 잔액을 초과합니다.' };

  if (cashType && cashName) {
    var w = withdrawFromAccount_(ss, cashType, cashName, amount, '');
    if (!w.ok) return w;
  }

  debtSheet.getRange(row, 4).setValue(balance - amount);
  return { ok: true, msg: '' };
}

function executeDebtIncurrence_(ss, cashType, cashName, debtName, amount, debtTypeLabel) {
  if (!debtName) debtName = '신규 부채';

  var debtSheet = ss.getSheetByName('부채');
  if (!debtSheet) return { ok: false, msg: '부채 시트가 없습니다.' };

  debtSheet.appendRow([debtTypeLabel || '기타', debtName, amount, amount, '', '', '', '', '자산_이동 자동등록']);

  if (cashType && cashName) {
    depositToAccount_(ss, cashType, cashName, amount, '');
  }

  return { ok: true, msg: '' };
}

function getAccountTotal_(ss, accountType, accountName) {
  var sheet = ss.getSheetByName('자산_종목');
  var lastRow = sheet.getLastRow();
  var total = 0;
  for (var r = 2; r <= lastRow; r++) {
    if (sheet.getRange(r, 1).getValue() !== accountType) continue;
    if (sheet.getRange(r, 2).getValue() !== accountName) continue;
    total += getRowValue_(sheet, r);
  }
  return total;
}

function getRowValue_(sheet, row) {
  var val = Number(sheet.getRange(row, 9).getValue());
  if (!isNaN(val) && val > 0) return val;
  var qty = Number(sheet.getRange(row, 6).getValue()) || 0;
  var price = Number(sheet.getRange(row, 8).getValue()) || 0;
  var fx = Number(sheet.getRange(row, 14).getValue()) || 1;
  return qty * price * fx;
}

function matchesStock_(sheet, row, stockName) {
  if (!stockName) return true;
  var ticker = String(sheet.getRange(row, 4).getValue() || '').trim();
  var name = String(sheet.getRange(row, 5).getValue() || '').trim();
  return ticker === stockName || name === stockName;
}

function withdrawFromAccount_(ss, accountType, accountName, amount, stockName) {
  var sheet = ss.getSheetByName('자산_종목');
  var remaining = amount;
  var lastRow = sheet.getLastRow();

  for (var r = 2; r <= lastRow && remaining > 0; r++) {
    if (sheet.getRange(r, 1).getValue() !== accountType) continue;
    if (sheet.getRange(r, 2).getValue() !== accountName) continue;
    if (!matchesStock_(sheet, r, stockName)) continue;

    var rowVal = getRowValue_(sheet, r);
    if (rowVal <= 0) continue;

    var qty = Number(sheet.getRange(r, 6).getValue()) || 0;
    var price = Number(sheet.getRange(r, 8).getValue()) || 0;

    if (rowVal <= remaining) {
      remaining -= rowVal;
      sheet.getRange(r, 6).setValue(0);
      sheet.getRange(r, 8).setValue(0);
    } else {
      if (qty <= 1) {
        sheet.getRange(r, 8).setValue(Math.max(0, price - remaining / qty));
      } else if (price > 0) {
        var sellQty = Math.min(qty, Math.ceil(remaining / (price * (Number(sheet.getRange(r, 14).getValue()) || 1))));
        sheet.getRange(r, 6).setValue(Math.max(0, qty - sellQty));
      }
      remaining = 0;
    }
  }

  if (remaining > 1) {
    return { ok: false, msg: '출발 계좌 잔액 부족 (부족: ' + Math.round(remaining).toLocaleString() + '원)' };
  }
  return { ok: true, msg: '' };
}

function depositToAccount_(ss, accountType, accountName, amount, stockName) {
  var sheet = ss.getSheetByName('자산_종목');
  var lastRow = sheet.getLastRow();

  for (var r = 2; r <= lastRow; r++) {
    if (sheet.getRange(r, 1).getValue() !== accountType) continue;
    if (sheet.getRange(r, 2).getValue() !== accountName) continue;
    if (!matchesStock_(sheet, r, stockName)) continue;

    var qty = Number(sheet.getRange(r, 6).getValue()) || 0;
    var price = Number(sheet.getRange(r, 8).getValue()) || 0;
    if (qty <= 0) qty = 1;

    if (String(sheet.getRange(r, 4).getValue() || '').trim() === '') {
      sheet.getRange(r, 8).setValue(price + amount / qty);
      return;
    }
  }

  appendAssetRow_(ss, accountType, accountName, stockName || accountName, amount);
}

function appendAssetRow_(ss, accountType, accountName, itemName, amount) {
  var sheet = ss.getSheetByName('자산_종목');
  sheet.appendRow([accountType, accountName, '공동', '', itemName, 1, amount, amount, '', '', '', '', 'KRW', '']);
}

function zeroOutAccount_(ss, accountType, accountName) {
  var sheet = ss.getSheetByName('자산_종목');
  var lastRow = sheet.getLastRow();
  for (var r = 2; r <= lastRow; r++) {
    if (sheet.getRange(r, 1).getValue() === accountType && sheet.getRange(r, 2).getValue() === accountName) {
      sheet.getRange(r, 6).setValue(0);
      sheet.getRange(r, 8).setValue(0);
    }
  }
}

function findDebtRow_(debtSheet, debtName) {
  if (!debtSheet) return -1;
  var data = debtSheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    if (String(data[i][1]) === debtName) return i + 1;
  }
  return -1;
}
