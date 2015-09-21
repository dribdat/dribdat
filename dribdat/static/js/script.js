(function($, window) {

  $(document).ready(function() {
    $('.event-countdown').each(function() {
      var clock = $(this).FlipClock({
        clockFace: 'DailyCounter'
      });
      var startdate = $(this).data('start');
      var datenow = Date.now();
      var timeleft = Date.parse(startdate) - datenow;
      clock.setTime(timeleft/1000);
      clock.setCountdown(true);
    });
  });

}).call(this, jQuery, window);
