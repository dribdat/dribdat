(function($, window) {

  $(document).ready(function() {
    $('.event-countdown').each(function() {
      var clock = $(this).FlipClock({
        clockFace: 'DailyCounter'
      });
      var timeleft = Date.parse($(this).data('start'))-Date.now();
      clock.setTime(timeleft/1000);
      clock.setCountdown(true);
    });
  });

}).call(this, jQuery, window);
