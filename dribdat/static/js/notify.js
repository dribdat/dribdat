(function($, window) {

  // Create a notification with the given title
  function createNotification() {
    $.get('/api/event/current/get/status', function(result) {
      //console.log(result);
      if (result.status) {
        let eventStatus = localStorage.getItem('eventstatus');
        if (eventStatus == result.status) return;

        eventStatus = result.status;
        localStorage.setItem('eventstatus', eventStatus);

        // Create and show the notification
        window.alert(eventStatus);
        $('#notifications-status-text').html(eventStatus);
      }
    });
  };

  if (location.href.indexOf('/dashboard')<0) {
    createNotification();
    setInterval(createNotification, 30 * 1000); // check once a minute
  }

}).call(this, jQuery, window);
