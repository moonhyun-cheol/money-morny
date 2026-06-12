/**
 * Yahoo Finance 시세 갱신 (국내 + 해외)
 */

function refreshStockPrices() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var assetSheet = ss.getSheetByName('자산_종목');
  if (!assetSheet) {
    showToast_('자산_종목 시트를 찾을 수 없습니다.');
    return;
  }

  var lastRow = assetSheet.getLastRow();
  if (lastRow < 2) {
    showToast_('갱신할 종목이 없습니다.');
    return;
  }

  var colCount = Math.max(13, assetSheet.getLastColumn());
  var data = assetSheet.getRange(2, 1, lastRow, colCount).getValues();
  var updated = 0;
  var failed = 0;

  for (var i = 0; i < data.length; i++) {
    var code = String(data[i][3] || '').trim();
    if (!code) continue;

    var market = String(data[i][11] || '').trim();
    var currency = String(data[i][12] || '').trim();
    if (!market && currency === 'USD') market = 'US';
    if (!market && currency === 'CNY') market = 'CN';
    if (!market && currency === 'KRW') market = 'KS';

    var price = fetchStockPrice_(code, market);
    if (price !== null) {
      assetSheet.getRange(i + 2, 8).setValue(price);
      updated++;
    } else {
      failed++;
    }
    Utilities.sleep(300);
  }

  updateQuotesSheet_(ss);
  showToast_('시세 갱신: ' + updated + '건 성공, ' + failed + '건 실패');
}

function fetchStockPrice_(code, market) {
  var symbol;
  if (market === 'US' || market === 'NASDAQ' || market === 'NYSE') {
    symbol = code;
  } else if (market === 'CN') {
    if (code.indexOf('.') >= 0) {
      symbol = code;
    } else {
      symbol = code + '.SS';
    }
  } else if (market === 'KQ') {
    symbol = code + '.KQ';
  } else if (market === 'HK') {
    symbol = code + '.HK';
  } else if (market === 'JP') {
    symbol = code + '.T';
  } else if (market === 'EU') {
    symbol = code;
  } else {
    symbol = code + '.KS';
  }

  var url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + encodeURIComponent(symbol) + '?interval=1d&range=1d';

  try {
    var response = UrlFetchApp.fetch(url, {
      muteHttpExceptions: true,
      headers: { 'User-Agent': 'Mozilla/5.0' },
    });
    if (response.getResponseCode() !== 200) return null;

    var json = JSON.parse(response.getContentText());
    var result = json.chart && json.chart.result && json.chart.result[0];
    if (!result || !result.meta) return null;

    var price = result.meta.regularMarketPrice || result.meta.previousClose;
    return price ? Number(price) : null;
  } catch (e) {
    Logger.log('시세 조회 실패: ' + symbol + ' — ' + e.message);
    return null;
  }
}

function updateQuotesSheet_(ss) {
  var assetSheet = ss.getSheetByName('자산_종목');
  var quoteSheet = ss.getSheetByName('시세');
  if (!quoteSheet || !assetSheet) return;

  var lastRow = assetSheet.getLastRow();
  var seen = {};
  var rows = [];

  for (var r = 2; r <= lastRow; r++) {
    var code = String(assetSheet.getRange(r, 4).getValue() || '').trim();
    if (!code || seen[code]) continue;
    seen[code] = true;
    var name = assetSheet.getRange(r, 5).getValue();
    var market = assetSheet.getRange(r, 12).getValue() || 'KS';
    var currency = assetSheet.getRange(r, 13).getValue() || 'KRW';
    var price = assetSheet.getRange(r, 8).getValue();
    rows.push([code, name, market + '/' + currency, price, new Date()]);
  }

  if (quoteSheet.getLastRow() > 1) {
    quoteSheet.getRange(2, 1, quoteSheet.getLastRow() - 1, 5).clearContent();
  }
  if (rows.length > 0) {
    quoteSheet.getRange(2, 1, rows.length, 5).setValues(rows);
  }
}
