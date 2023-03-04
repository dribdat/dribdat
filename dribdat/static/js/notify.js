(function($, window) {

  // Bootup
  $notificationBtn = $('#notification-button');
  if (Notification.permission === 'denied' || Notification.permission === 'default') {
    $notificationBtn.show();
  } else {
    $notificationBtn.hide();
  }

  function askNotificationPermission(e) {
    console.log('Asking...')
    e.preventDefault();
    e.stopPropagation();
    // Function to actually ask the permissions
    function handlePermission(permission) {
      // Whatever the user answers, we make sure Chrome stores the information
      if (!Reflect.has(Notification, 'permission')) {
        Notification.permission = permission;
      }
      // Set the button to shown or hidden, depending on what the user answers
      if (Notification.permission === 'denied' || Notification.permission === 'default') {
        $notificationBtn.show();
      } else {
        $notificationBtn.hide();
      }
    };

    // Check if the browser supports notifications
    if (!Reflect.has(window, 'Notification')) {
      console.info('This browser does not support notifications.');
    } else {
      if (checkNotificationPromise()) {
        Notification.requestPermission().then(handlePermission);
      } else {
        Notification.requestPermission(handlePermission);
      }
    }
  };

  // Check whether browser supports the promise version of requestPermission()
  // Safari only supports the old callback-based version
  function checkNotificationPromise() {
    try {
      Notification.requestPermission().then();
    } catch(e) {
      return false;
    }
    return true;
  };

  // Wire up notification permission functionality to 'Enable notifications' button
  $notificationBtn.on('click', askNotificationPermission);

  // Create a notification with the given title
  function createNotification() {
    const text = 'Hello, world!'
    // Create and show the notification
    const img = '/static/img/logo11.png';
    const notification = new Notification('Dribdat', { body: text, icon: img });
    console.log('Sent...')
  };

  setInterval(createNotification, 3000);

}).call(this, jQuery, window);
