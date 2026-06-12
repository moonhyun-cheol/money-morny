/**
 * 환율 갱신 (Yahoo Finance) — USD, CNY(위안)
 * CNY/KRW = USDKRW ÷ USDCNY (1위안당 원화)
 */

function refreshFxRates() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('환율');
  if (!sheet) {
    showToast_('환율 시트가 없습니다.');
    return;
  }

  var now = new Date();
  var updated = 0;

  var usdKrw = fetchFxRate_('USDKRW=X');
  if (usdKrw !== null) {
    sheet.getRange(2, 2).setValue(usdKrw);
    sheet.getRange(2, 4).setValue(now);
    updated++;
  }

  var usdCny = fetchFxRate_('USDCNY=X');
  if (usdKrw !== null && usdCny !== null && usdCny > 0) {
    var cnyKrw = usdKrw / usdCny;
    sheet.getRange(3, 2).setValue(Math.round(cnyKrw * 100) / 100);
    sheet.getRange(3, 4).setValue(now);
    updated++;
  } else {
    var direct = fetchFxRate_('CNHKRW=X');
    if (direct !== null) {
      sheet.getRange(3, 2).setValue(direct);
      sheet.getRange(3, 4).setValue(now);
      updated++;
    }
  }

  showToast_('환율 갱신: ' + updated + '/2 (USD, CNY)');
}

function fetchFxRate_(symbol) {
  var url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + symbol + '?interval=1d&range=1d';
  try {
    var response = UrlFetchApp.fetch(url, {
      muteHttpExceptions: true,
      headers: { 'User-Agent': 'Mozilla/5.0' },
    });
    if (response.getResponseCode() !== 200) return null;
    var json = JSON.parse(response.getContentText());
    var meta = json.chart && json.chart.result && json.chart.result[0] && json.chart.result[0].meta;
    var price = meta && (meta.regularMarketPrice || meta.previousClose);
    return price ? Number(price) : null;
  } catch (e) {
    Logger.log('환율 실패: ' + symbol + ' — ' + e.message);
    return null;
  }
}

function refreshAllMarketData() {
  refreshFxRates();
  refreshStockPrices();
  takeDailyAssetSnapshot();
}
