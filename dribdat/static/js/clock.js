(function($, window) {

  $(document).ready(function() {

    // Initialise home page countdown
    $('.event-countdown').each(function() {
      var startdate = $(this).data('start');
      var datenow = Date.now();
      var datesched = Date.parse(startdate.replace(' ', 'T'));
      var timeleft = datesched - datenow;
      if (isNaN(timeleft) || timeleft < 0) return;

      var clock = new FlipClock(this, new Date(datesched), {
        face: 'DayCounter',
        countdown: true
      });
      // clock.setCountdown(true);
    });

  });

}).call(this, jQuery, window);
