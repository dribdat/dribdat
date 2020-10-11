(function($, window) {

  $(document).ready(function() {

    // Detect and recommend SSL connection
    if ('https:' != document.location.protocol)
      $('footer').before('<center class="alert alert-default" style="margin-top:2em" role="alert">&#x1f525; Your connection to this website is insecure. <a href="https:' + window.location.href.substring(window.location.protocol.length) + '" class="btn btn-sm btn-warning"><b>Switch to HTTPS</b></a></center>');

    // Initialise home page countdown
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

  // Initialize project data loader
  $('#autotext_url').each(function() {

    var supported = false;

    var checkAutotext = function(val, $ind) {
      if (typeof val !== 'string') return;
      if (val.trim() === '') return;
      supported = (
        val.indexOf('datapackage.json') > 0 ||
        val.indexOf('//github.com/') > 0 ||
        val.indexOf('//gitlab.com/') > 0 ||
        val.indexOf('//bitbucket.org/') > 0 ||
        val.indexOf('document') > 0 ||
        val.indexOf('wiki') > 0 ||
        val.indexOf('/p/') > 0
      );
      $ind.find('i')
        .removeClass('fa-circle-o fa-check-circle-o')
        .addClass(!supported ? 'fa-circle-o' : 'fa-check-circle-o')
        .css('color', (supported ? 'green' : 'red'));
      $ind.find('.autotext-indicator')
        .css('visibility', (supported ? '' : 'hidden'));
      $('#is_autoupdate').click(function() {
        if ($(this).is(':checked'))
          if (!$indicator.find('button').click())
            $(this).click();
      });
    };
    // Toggle status indicator
    var $inputfield = $(this);
    var $indicator = $inputfield.parent()
      .append('<span class="autotext-indicator" style="visibility:hidden">' +
        '<i style="color:red" class="fa fa-circle-o"></i>&nbsp;' +
        '<button type="button">Update now</button>' +
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

      /* Warning no longer needed -
      if ($('input#name').val() && !window.confirm('All project fields (Title, etc.) ' +
        'will be overwritten with remote project data. Proceed?')) {
          if ($('#is_autoupdate').is(':checked')) $('#is_autoupdate').click();
          return false;
        }
      */

      var $button = $(this);
      $indicator.find('i').css('color', 'blue');
      $button.attr('disabled', 'disabled').html('Please wait ...');
      $.getJSON('/api/project/autofill?url=' + url, function(data) {
        $indicator.find('i').css('color', 'green');
        $button.removeAttr('disabled').html('Update now');

        if (typeof data.name === 'undefined' || data.name === '') {
          window.alert('Project data could not be fetched - enter a valid Remote link.');
          $('#is_autoupdate').prop('checked', false);
          return;
        }

        if (!$('input#name').val())
          $('input#name').val(data.name);
        if (!$('input#summary').val())
          $('input#summary').val(data.summary);
        if (!$('input#webpage_url').val())
          $('input#webpage_url').val(data.homepage_url);
        if (!$('input#source_url').val())
          $('input#source_url').val(data.source_url);
        if (!$('input#contact_url').val())
          $('input#contact_url').val(data.contact_url);
        if (!$('input#image_url').val())
          $('input#image_url').val(data.image_url);
      });
      return true;
    });
  });

  // Make the custom color field HTML5 compatible
  $('input#logo_color[type=text]').attr('type', 'color');

  // Open up the README on click
  $('.project-autotext').click(function() {
    $(this).addClass('active');
  });

  // Post a project update
  $('.project-post').click(function() {

  });

  // Clickable categories navigation
  var $navCategories = $('.nav-categories .btn-group label').click(function(e) {
    $(this).parent().find('.active').removeClass('active');
    $(this).parent().addClass('active');
    var selected_id = $(this).find('input').attr('id');
    var $projects = $('.honeycomb .project');
    var $infotext = $('.category-info');
    $('.honeycomb').removeClass('hide-challenges');

    if (selected_id === '' || selected_id === 'list' || selected_id === 'challenges') {
      $projects.addClass('category-highlight');
      $('.category-container', $infotext).hide();
      $projects
        .removeClass('hexagon hexalist')
        .addClass(selected_id === 'list' ? 'hexalist' : 'hexagon');
      if (selected_id === 'challenges')
        $('.honeycomb').addClass('hide-challenges');

    } else {
      var $selected = $('[category-id="' + selected_id + '"]', $projects.parent());
      $projects.removeClass('category-highlight');
      $selected.addClass('category-highlight');
      $('.category-container', $infotext).hide();
      $('[category-id="' + selected_id + '"]', $infotext).show();
    }
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

  // Show project history
  $('#show-history').click(function(e) {
    e.preventDefault(); e.stopPropagation();
    $('.details .history').slideDown();
  });
  $('.details .history').hide();

  // Make embedded iframes resizable
  $('.resizable').each(function() {
    var $self = $(this);
    // Yech. Because script loading order
    // and this whole UI needs a refresh.
    $(window).on('load', function() {
      $self.resizable({
        resizeWidth: false,
        handleSelector: ".win-size-grip"
      });
    });
  });

}).call(this, jQuery, window);
