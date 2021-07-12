(function($, window) {

  // Initialize project data loader
  $('#autotext_url').each(function() {

    var checkAutotext = function(val, $ind) {
      if (typeof val !== 'string') return;
      if (val.trim() === '') return;
      $ind.find('i')
        .removeClass('fa-circle-o fa-check-circle-o')
        .addClass('fa-check-circle-o')
        .css('color', 'red');
      $ind
        .css('visibility', '');
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
        '<button type="button">Fetch content</button>' +
      '</span>')
      .find('.autotext-indicator');

    // On load
    checkAutotext($inputfield.val(), $indicator);

    // On keypress
    $inputfield.on('keyup', function(e) {
      checkAutotext($inputfield.val(), $indicator);
    });

    // Update button
    $indicator.find('button').click(function(e) {
      e.preventDefault();
      e.stopPropagation();
      var url = $inputfield.val();
      var $button = $(this);
      $indicator.find('i').css('color', 'blue');
      $button.attr('disabled', 'disabled').html('Please wait ...');
      // Call updater API
      $.getJSON('/api/project/autofill?url=' + url, function(data) {
        $indicator.find('i').css('color', 'green');
        $button.removeAttr('disabled').html('Update now');
        if (typeof data.name === 'undefined' || data.name === '') {
          window.alert('Enter a valid link to sync from a supported site.');
          $('#is_autoupdate').prop('checked', false);
          return;
        }
        // Set form values
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
        if (!$('input#download_url').val())
          $('input#download_url').val(data.download_url);
        if (!$('input#image_url').val())
          $('input#image_url').val(data.image_url);
      });
      return true;
    });
  });

  // Allow project progress on acknowledge
  $('.form-project-post label[for="has_progress"]').each(function() {
    var vparent = $(this).parent().parent().hide();
    var vinput = $(this).parent().find('input')[0];
    vinput.checked = false;
    $('.form-project-stage input[type="checkbox"]').click(function() {
      vparent.show();
      all_checked = $('.form-project-stage input[type="checkbox"]:not(:checked)').length === 0;
      vinput.checked = all_checked;
    });
  });

  // Make the custom color field HTML5 compatible
  $('input#logo_color[type=text]').attr('type', 'color');

  // Open up the README on click
  $('.project-autotext').click(function() {
    $(this).addClass('active');
  });

  // Check image size on render
  $('.project-home .project-image-container').each(function() {
    var $self = $(this);
    var url = $self.data('href');
    if (url.length<6) return;
    var img = new Image();
    img.onload = function() {
      if (this.width > this.height > 512 || this.width > 640)
        return $self.addClass('overlay');
      this.id = 'overlayImage';
      $self.addClass('underlay').after(this);
    }
    img.src = url;
  });

  // Upload images
  $('#uploadImage').each(function() {
    var $togglebtn = $('button[data-target="#uploadImage"]');
    $('.fld-longtext').append($togglebtn);
    $('.fld-image_url').append($togglebtn.clone());
    var $dialog = $(this);
    var $inputfd = $dialog.find('input[type="file"]');
    $inputfd.change(function() {
      var imgfile = $inputfd[0].files[0];
      // Check file size limits
      var maxsize = parseInt($inputfd.data('maxsize'));
      if (imgfile.size > maxsize) {
        return alert("Please upload a smaller file (1 MB limit)");
      }
      // Create upload object
      var fdd = new FormData();
      fdd.append('file', imgfile);
      $.ajax({
        url: '/api/project/uploader',
        type: 'post',
        data: fdd,
        processData: false,
        contentType: false,
        success: function(response) {
          if (response.indexOf('http') !== 0) {
             return alert('File could not be uploaded :(\n' + response);
          }
          $dialog.find(".preview img").attr("src", response);
          $dialog.find(".preview input").val(response);
          $dialog.find(".hidden").show();
          $('#img-confirm').show().find('button').click(function() {
            if ($(this).data('target') == 'cover') {
              // Replace the cover
              $('#image_url').val(response);
              $dialog.modal('hide');
            } else if ($(this).data('target') == 'pitch') {
              // Append to pitch
              $('#longtext').val($('#longtext').val() +
                '\n\n' + '![Title](' + response + ')');
              $dialog.modal('hide');
            } else {
              // Copy to clipboard
              if (navigator.clipboard) {
                navigator.clipboard.writeText(response);
                $dialog.modal('hide');
              } else {
                $dialog.find(".preview input").click().select();
                document.execCommand("copy");
              }
            }
          });
        },
        error: function(e) {
          alert("Sorry, an error has occurred.\n" + e.statusText);
        }
      }); // -ajax
    }); // -change
  }); // -#uploadImage

  // Simple delay function, thanks to Christian C. Salvadó
  function delay(callback, ms) {
    var timer = 0;
    return function() {
      var context = this, args = arguments;
      clearTimeout(timer);
      timer = setTimeout(function () {
        callback.apply(context, args);
      }, ms || 0);
    };
  }

  // About page simple stupid search
  var lastSearch = null;
  var searchForm = $('form#search');
  searchForm.find('input[name="q"]')
    .keyup(delay(function(e) {
      if (e.keyCode == 13) { e.preventDefault(); return false; }
      var q = $(this).val();
      if (q.length < 4 || q.trim() == lastSearch) return;
      lastSearch = q.trim();
      $ul = $('#search-results').empty();
      $.get(searchForm.attr('action') + '?q=' + q, function(d) {
        d.projects.forEach(function(p) {
          $ul.append(
            '<a class="col-5 card project"' +
               'href="' + p.url + '">' +
              '<div class="card-body">' +
                '<h5 class="card-title">' + p.name + '</h5>' +
                '<p class="card-text">' + p.summary + '</p>' +
              '</div>' +
            '</a>'
          );
        });
      });
    }, 500));

  // Clickable categories navigation
  var $navCategories = $('.nav-categories .btn-group label').click(function(e) {
    $(this).parent().find('.active').removeClass('active');
    $(this).parent().addClass('active');
    var selected_id = $(this).find('input').attr('id');
    var $projects = $('.honeycomb .project');
    var $infotext = $('.category-info');
    $('.honeycomb').removeClass('hide-challenges');

    if (selected_id === '' || selected_id === 'list' || selected_id === 'challenges') {
      // Visibility option selected
      $projects.addClass('category-highlight');
      $('.category-container', $infotext).hide();
      $projects
        .removeClass('hexagon hexalist')
        .addClass(selected_id === 'list' ? 'hexalist' : 'hexagon');
      if (selected_id !== '')
        $('.honeycomb').addClass('hide-challenges');

    } else {
      // A category is selected
      var $selected = $('[category-id="' + selected_id + '"]', $projects.parent());
      $projects.removeClass('category-highlight');
      $selected.addClass('category-highlight');
      $('.category-container', $infotext).hide();
      $('[category-id="' + selected_id + '"]', $infotext).show();
    }
  });
  // Toggle challenges after the hackathon
  // $('.event-finished .nav-categories #challenges').parent().click();

  // Roll up categories if there is only one, and no projects
  if ($navCategories.length === 1)
    $navCategories.click().parent().parent().hide();

  // Show embed code when button clicked
  $('#embed-link').click(function(e) {
    e.preventDefault(); e.stopPropagation();
    var url = $(this).attr('href') + '?embed=1';
    var code = '<iframe src="' + url + '" style="width:100%;height:320px;background:transparent;border:none;overflow:hidden" scrolling="no"></iframe>';
    window.prompt('Share the event link in social media, or copy and paste this HTML code to embed on your site. For even better embedding, visit github.com/dribdat/backboard', code);
  });

  // Horizontal desktop dragging of project pages
  $('.profile-projects').each(function() {
    const ele = $(this)[0];
    // thanks to Nguyen Huu Phuoc
    ele.style.cursor = 'grab';
    let pos = { top: 0, left: 0, x: 0, y: 0 };
    const mouseDownHandler = function(e) {
        ele.style.cursor = 'grabbing';
        ele.style.userSelect = 'none';
        pos = {
            left: ele.scrollLeft,
            top: ele.scrollTop,
            // Get the current mouse position
            x: e.clientX,
            y: e.clientY,
        };
        document.addEventListener('mousemove', mouseMoveHandler);
        document.addEventListener('mouseup', mouseUpHandler);
    };
    const mouseMoveHandler = function(e) {
        const dx = e.clientX - pos.x;
        const dy = e.clientY - pos.y;
        ele.scrollTop = pos.top - dy;
        ele.scrollLeft = pos.left - dx;
    };
    const mouseUpHandler = function() {
        ele.style.cursor = 'grab';
        ele.style.removeProperty('user-select');
        document.removeEventListener('mousemove', mouseMoveHandler);
        document.removeEventListener('mouseup', mouseUpHandler);
    };
    ele.addEventListener('mousedown', mouseDownHandler);
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

  // Admin button tips
  $('.admin-defaults button').click(function() {
    $('input#name').val($(this).text());
  });

  // Ye olde darke moude
  function setDarkMode(toggle) {
    dm = Boolean(window.darkmode);
    if (toggle) dm = !dm;
    if (dm) {
      $('html').css('-webkit-filter','invert(100%)')
               .css('-moz-filter','invert(100%)')
               .css('-o-filter','invert(100%)')
               .css('-ms-filter','invert(100%)')
               .css('background', 'black')
               .css('height', '100%');
    } else {
      $('html').attr('style','');
    }
    localStorage.setItem('darkmode', dm ? '1' : '0');
    window.darkmode = dm;
  }
  window.darkmode = localStorage.getItem('darkmode') == '1';
  setDarkMode(false);
  // Enable dark mode on click
  $('.darkmode').click(function(e) {
    e.preventDefault(); e.stopPropagation();
    setDarkMode(true);
  });

}).call(this, jQuery, window);
