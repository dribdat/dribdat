(function($, window) {


$('#announcements button').click(function() {
  let $self = $(this);
  let message = $('#announcements textarea').val();
  if (message.length == 0) {
    if (!window.confirm(
      'Cancel broadcast?'
    )) return false;
  } else { 
    if (!window.confirm(message.substr(0, 20) +
      '\n-------------------------\n' +
      'Ready to broadcast this? The rest of the message ' +
      'will be shown in the window, the first 20 bytes as title.'
    )) return false;
  }
  //console.log(message);
  $.post('/api/event/current/push/status', {
    'text': message
  }, function(resp) {
    if (resp.status && resp.status == 'OK') {
      $self.html('✅ Sent');
      setTimeout(function() {
        $self.html('📣');
      }, 5000);
    } else {
      console.error(resp);
    }
  });
});


}).call(this, jQuery, window);
