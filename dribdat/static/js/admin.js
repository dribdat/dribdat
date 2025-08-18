(function($, window) {

if (typeof vegaEmbed !== 'undefined') {

  $.getJSON('/api/event/current/activity.json?limit=200', function(data) {
    if (data.activities.length == 0)
        return $('#activities').hide();
    var yourVlSpec = {
      "width": "720",
      "$schema": "https://vega.github.io/schema/vega-lite/v2.0.json",
      "title": "Activity",
      "data": {
        "values": data.activities
      },
      "mark": {
        "type": "bar"
      },
      "encoding": {
        "x": {
          "field": "date",
          "type": "temporal",
          "scale": { "rangeStep": null }
        },
        "y": {
          "aggregate": "mean",
          "field": "project_score",
          "type": "quantitative",
          "axis": { "title": "score", "labels": true }
        }
      },
      "config": {
        "autosize": { "type": "fit", "contains": "padding" },
        "axis": { "grid": true, "ticks": false }
      }
    }
    vegaEmbed("#activities", yourVlSpec);
  });
}

$('#announcements button').click(function() {
  let $self = $(this);
  let message = $('#announcements textarea').val();
  if (message.length == 0) {
    if (!window.confirm(
      'Cancel broadcast?'
    )) return false;
  } else { 
    if (!window.confirm(message +
      '\n-------------------------\n' +
      'Ready to broadcast this?'
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
