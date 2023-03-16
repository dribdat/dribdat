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
        $('#global-notifications-alert').removeClass('hidden');
      }
    });
  };

  if (location.href.indexOf('/dashboard')<0) {
    createNotification();
    setInterval(createNotification, 30 * 1000); // check once a minute
  }

  $('#notification-button').click(function() {
    let eventNotify = localStorage.getItem('eventstatus-notify');
    localStorage.setItem('eventstatus-notify', true);
  });

}).call(this, jQuery, window);
