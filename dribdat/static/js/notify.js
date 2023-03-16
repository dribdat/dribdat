(function($, window) {

  // Create a notification with the given title
  function createNotification() {
    $.get('/api/event/current/get/status', function(result) {
      //console.log(result);
      if (result.status) {
        // Retrieve the previous event status
        let eventStatus = localStorage.getItem('eventstatus');

        // If there is no change in status, exit here..
        if (eventStatus == result.status) return;

        // Get the new status text and save it in the browser storage
        eventStatus = result.status;
        localStorage.setItem('eventstatus', eventStatus);

        // Update the HTML widgets with new message
        $('#notifications-status-text').html(eventStatus);
        $('#global-notifications-alert').removeClass('hidden');

        setTimeout(function() {
          // Create and show the notification
          let userOptOut = localStorage.getItem('eventstatus-mute');
          if (!userOptOut) {
            userOptOut = !window.confirm(eventStatus + 
              '\n\n(OK to see more alerts like this?)');
          }

          if (userOptOut) {
            // Stop showing prompts in the future
            //console.log('muting...');
            localStorage.setItem('eventstatus-mute', 1);
          }
        }, 500);
      }
    });
  };

  // Check the location, ignore the Dashboard
  if (location.href.indexOf('/dashboard')<0) {
    createNotification();
    setInterval(createNotification, 30 * 1000); // check twice a minute

    // To enable the popups, click the button in the footer
    $('#notification-button').show().click(function() {
      //console.log('un-muting...');
      localStorage.removeItem('eventstatus-mute');
      localStorage.removeItem('eventstatus');
      createNotification();
    });

  } // -no-dashboard

}).call(this, jQuery, window);
