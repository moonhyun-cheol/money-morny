/**
 * 시간 기반 트리거
 */

function installTriggers() {
  removeTriggers();

  ScriptApp.newTrigger('checkEndOfMonthAndRun_')
    .timeBased()
    .everyDays(1)
    .atHour(23)
    .create();

  ScriptApp.newTrigger('refreshAllMarketData')
    .timeBased()
    .everyDays(1)
    .atHour(9)
    .create();

  ScriptApp.newTrigger('checkDailyAlerts_')
    .timeBased()
    .everyDays(1)
    .atHour(8)
    .create();

  showToast_('트리거 설치: 8시 만기알림, 9시 시세·환율·일별자산, 23시 월말');
}

function removeTriggers() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    ScriptApp.deleteTrigger(triggers[i]);
  }
  showToast_('트리거 제거 완료');
}
