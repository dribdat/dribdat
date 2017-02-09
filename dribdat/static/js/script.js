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

    var supported = false;

    var checkAutotext = function(val, $ind) {
      if (typeof val !== 'string') return;
      supported = (
        val.indexOf('//github.com/') > 0 ||
        val.indexOf('//bitbucket.org/') > 0 ||
        val.indexOf('//make.opendata.ch/wiki/') > 0
      );
      $ind.find('i')
        .removeClass('fa-circle-o fa-check-circle-o')
        .addClass(!supported ? 'fa-circle-o' : 'fa-check-circle-o')
        .css('color', (supported ? 'green' : 'red'));
      $ind.find('button')
        .css('visibility', (supported ? '' : 'hidden'));
      $('#is_autoupdate').click(function() {
        if ($(this).is(':checked'))
          if (!$indicator.find('button').click())
            $(this).click();
      });
    };

    var $inputfield = $(this);
    var $indicator = $inputfield.parent()
      .append('<span class="autotext-indicator">' +
        '<i style="color:red" class="fa fa-circle-o"></i>&nbsp;' +
        '<button type="button" style="visibility:hidden">Update now</button>' +
      '</span>')
      .find('.autotext-indicator');

    // On load
    checkAutotext($inputfield.val(), $indicator);

    // On keypress
    $inputfield.on('keyup', function(e) {
      checkAutotext($inputfield.val(), $indicator);
    });

    $indicator.find('button').click(function(e) {
      e.preventDefault();
      e.stopPropagation();
      var url = $inputfield.val();

      if ($('input#name').val() && !window.confirm('All project fields (Title, etc.) ' +
        'will be overwritten with remote project data. Proceed?')) {
          if ($('#is_autoupdate').is(':checked')) $('#is_autoupdate').click();
          return false;
        }

      var $button = $(this);
      $indicator.find('i').css('color', 'blue');
      $button.attr('disabled', 'disabled').html('Please wait ...');
      $.getJSON('/project/autofill?url=' + url, function(data) {
        $indicator.find('i').css('color', 'green');
        $button.removeAttr('disabled').html('Update now');

        if (typeof data.name === 'undefined' || data.name === '') {
          window.alert('Project data could not be fetched - enter a valid Remote link.');
          $('#is_autoupdate').prop('checked', false);
          return;
        }

        $('input#name').val(data.name);
        $('input#summary').val(data.summary);
        $('textarea#longtext').html(data.description);
        $('input#webpage_url').val(data.homepage_url);
        $('input#source_url').val(data.source_url);
        $('input#contact_url').val(data.contact_url);
        $('input#image_url').val(data.image_url);
      });
      return true;
    });
  });

  // Make the custom color field HTML5 compatible
  $('input#logo_color[type=text]').attr('type', 'color');

  // Clickable categories navigation
  var $navCategories = $('.nav-categories .btn-group label').click(function(e) {
    var selected_id = $(this).find('input').attr('id');
    var $projects = $('.honeycomb .project');
    var $infotext = $('.category-info');
    if (selected_id === 'challenges') {
      // pass
    } else if (selected_id === '' || selected_id === 'list') {
      $projects.css('opacity', 1.0);
      $('.category-container', $infotext).hide();
      $projects
        .removeClass('hexagon hexalist')
        .addClass(selected_id === 'list' ? 'hexalist' : 'hexagon');
    } else {
      var $selected = $('[category-id="' + selected_id + '"]', $projects.parent());
      $projects.css('opacity', 0.4);
      $selected.css('opacity', 1.0);
      $('.category-container', $infotext).hide();
      $('[category-id="' + selected_id + '"]', $infotext).show();
    }
    setTimeout(function() {
      var challenges_on = $('#challenges').is(':checked');
      $('.honeycomb').removeClass('hide-challenges')
        .addClass(challenges_on ? '' : 'hide-challenges');
      $('#challenges').parent().removeClass('active')
        .addClass(challenges_on ? 'active' : '');
    }, 1);
  });

  // Roll up categories if there is only one, and no projects
  if ($navCategories.length === 1)
    $navCategories.click().parent().parent().hide();

  // Show embed code when button clicked
  $('#embed-link').click(function(e) {
    e.preventDefault(); e.stopPropagation();
    var url = $(this).attr('href');
    var code = '<iframe src="' + url + '" style="width:100%;height:320px;background:transparent;border:none;overflow:hidden" scrolling="no"></iframe>';
    window.prompt('Copy and paste this code to embed this event:', code);
  });

}).call(this, jQuery, window);
