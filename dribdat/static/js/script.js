(function($, window) {

  $(document).ready(function() {
    $('.event-countdown').each(function() {
      var clock = $(this).FlipClock({
        clockFace: 'DailyCounter'
      });
      var startdate = $(this).data('start');
      var datenow = Date.now();
      var datesched = Date.parse(startdate.replace(' ', 'T'));
      var timeleft = datesched - datenow;
      if (isNaN(timeleft)) return;
      clock.setTime(timeleft/1000);
      clock.setCountdown(true);
    });
  });

  $('#autotext_url').each(function() {

    var checkAutotext = function(val, $ind) {
      if (typeof val !== 'string') return;
      var supported = (
        val.indexOf('//github.com/') > 0 ||
        val.indexOf('//bitbucket.com/') > 0 ||
        val.indexOf('//make.opendata.ch/wiki/') > 0
      );
      $ind.find('i')
        .removeClass('fa-circle-o fa-check-circle-o')
        .addClass(!supported ? 'fa-circle-o' : 'fa-check-circle-o')
        .css('color', (supported ? 'green' : 'red'));
      $ind.find('button')
        .css('visibility', (supported ? '' : 'hidden'));
    };

    var $inputfield = $(this);
    var $indicator = $inputfield.parent()
      .append('<span class="autotext-indicator">' +
        '<i style="color:red" class="fa fa-circle-o"></i>&nbsp;' +
        '<button style="visibility:hidden">Update now</button>' +
      '</span>')
      .find('.autotext-indicator');

    checkAutotext($inputfield, $indicator);
    $inputfield.on('keyup', function(e) {
      checkAutotext($inputfield.val(), $indicator);
    });
    $indicator.find('button').click(function(e) {
      e.preventDefault();
      e.stopPropagation();
      var url = $inputfield.val();

      var $button = $(this);
      $indicator.find('i').css('color', 'blue');
      $button.attr('disabled', 'disabled').html('Please wait ...');
      $.getJSON('/project/autofill?url=' + url, function(data) {
        $indicator.find('i').css('color', 'green');
        $button.removeAttr('disabled').html('Update now');

        $('input#name').val(data.name);
        $('input#summary').val(data.summary);
        $('textarea#longtext').html(data.description);
        $('input#webpage_url').val(data.homepage_url);
        $('input#source_url').val(data.source_url);
        $('input#image_url').val(data.image_url);
      });
    });

  });

}).call(this, jQuery, window);
