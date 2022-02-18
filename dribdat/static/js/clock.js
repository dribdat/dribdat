(function($, window) {

  $(document).ready(function() {

    // Initialise home page countdown
    $('.event-countdown').each(function() {
      var startdate = $(this).data('start');
      var datenow = Date.now();
      var datesched = Date.parse(startdate.replace(' ', 'T'));
      var timeleft = datesched - datenow;
      if (isNaN(timeleft) || timeleft < 0) return;
      var unixtime = datesched / 1000;
      // Start the clock
      new FlipDown(unixtime, $(this).attr('id')).start();
    });

  });

}).call(this, jQuery, window);
