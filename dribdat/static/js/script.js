(function($, window) {

  // Initialize project data loader
  $('#autotext_url').each(function() {

    var checkAutotext = function(val, $ind) {
      if (typeof val !== 'string') return;
      if (val.trim() === '') return;
      $ind
        .removeClass('d-none')
        .find('i')
          .removeClass('fa-circle-o fa-check-circle-o')
          .addClass('fa-check-circle-o')
          .css('color', 'red');
      $('#is_autoupdate').click(function() {
        if ($(this).is(':checked'))
          if (!$indicator.find('button').click())
            $(this).click();
      });
    };
    // Toggle status indicator
    var $inputfield = $(this);
    var $indicator = $inputfield.parent()
      .append('<span class="autotext-indicator d-none btn-group">' +
        '<a title="Status" class="btn btn-lg btn-light btn-disabled"><i class="fa fa-circle-o"></i></a>' +
        '<button class="btn btn-lg btn-warning" type="button">' +
        'Sync content</button>' +
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
        $button.removeAttr('disabled').html('Refresh');
        if (typeof data.name === 'undefined' || data.name === '') {
          window.alert('Enter a valid link to sync from a supported site.');
          $('#is_autoupdate').prop('checked', false);
          $indicator.find('i').css('color', 'red');
          return;
        }
        $indicator.find('i').css('color', 'green');
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
    $('.form-project-confirm input[type="checkbox"]').click(function() {
      vparent.show();
      all_checked = $('.form-project-confirm input[type="checkbox"]:not(:checked)').length === 0;
      vinput.checked = all_checked;
    });
  });

  // Make the custom color field HTML5 compatible
  $('input#logo_color[type=text]').attr('type', 'color');

  // Open up the README on click
  $('.project-autotext').click(function() {
    $(this).addClass('active');
  });

  // Open up the LOG if navigated
  if (window.location.hash == '#log' || window.location.pathname.endsWith('/log')) {
    $('#dribs-tab-md').click();
  }

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
    var $dialog = $(this);
    var $togglebtn = $('button[data-target="#uploadImage"]');
    // Enable the available fields
    var $longtext = $('.fld-longtext');
    var $imageurl = $('.fld-image_url');
    if ($longtext.length > 0) {
      $longtext.prepend($togglebtn.clone().show());
    } else {
      $dialog.find("[data-target='pitch']").hide();
    }
    if ($imageurl.length > 0) {
      $imageurl.append($togglebtn.clone().show());
    } else {
      $dialog.find("[data-target='cover']").hide();
    }
    // Set up the file dialog
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
              var imglink = '![Title](' + response + ')';
              if (typeof window.toasteditor !== 'undefined') {
                window.toasteditor.insertText(imglink);
              } else {
                $('#longtext').val($('#longtext').val() +
                  '\n\n' + imglink);
              }
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


  // Upload files
  $('#uploadFile').each(function() {
    var $dialog = $(this);
    var $togglebtn = $('button[data-target="#uploadFile"]');
    // Enable the available fields
    var $longtext = $('.fld-longtext');
    var $webpageurl = $('.fld-webpage_url');
    // Append button to the pitch editor
    $longtext.prepend($togglebtn.clone().show());
    // $webpageurl.append($togglebtn.clone().show());
    // Set up the file dialog
    var $inputfd = $dialog.find('input[type="file"]');
    $inputfd.change(function() {
      var thefile = $inputfd[0].files[0];
      // Check file size limits
      var maxsize = parseInt($inputfd.data('maxsize'));
      if (thefile.size > maxsize) {
        return alert("Please upload a smaller file (1 MB limit)");
      }
      // Create upload object
      var fdd = new FormData();
      fdd.append('file', thefile);
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
          var path = $inputfd.val();
          var filename = path.split(/(\\|\/)/g).pop();
          $dialog.find(".preview input").val(response);
          $dialog.find(".hidden").show();
          $('#file-confirm').show().find('button').click(function() {
            if ($(this).data('target') == 'weblink') {
              // Replace the cover
              $('#webpage_url').val(response);
              $dialog.modal('hide');
            } else if ($(this).data('target') == 'pitch') {
              // Append to pitch
              var fileLink = '📦 File: [' + filename + '](' + response + ')';
              if (typeof window.toasteditor !== 'undefined') {
                window.toasteditor.insertText(fileLink);
              } else {
                $('#longtext').val($('#longtext').val() +
                  '\n\n' + fileLink);
              }
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
  var searchForm = $('#search');
  var searchAction = searchForm.attr('action');
  var searchIgnore = searchForm.find('#id').val();
  searchForm.find('input[name="q"]')
    .keyup(delay(function(e) {
      if (e.keyCode == 13) { e.preventDefault(); return false; }
      runSearch($(this).val());
    }, 500));
  checkSearchQuery();

  // Post editor smart search
  $('.projectpost .form-project-post #note')
    .keyup(delay(function(e) {
      if (e.keyCode == 13) { e.preventDefault(); return false; }
      var lastWord = $(this).val();
      if (lastWord.length < 4) return false;
      lastWord = lastWord.trim().split(' ');
      if (lastWord.length < 1) return false;
      lastWord = lastWord[lastWord.length-1];
      runSearch(lastWord);
    }, 500));

  function runSearch(q) {
    if (q.length < 4 || q.trim() == lastSearch) return;
    lastSearch = q.trim();
    $.get(searchAction + '?q=' + q, function(d) {
      // Filter out the current project, if there is one
      var projects = d.projects;
      if (typeof searchIgnore !== undefined && searchIgnore) {
        const si = parseInt(searchIgnore);
        projects = projects.filter(function(d) { return d.id !== si });
      }
      // Reset search containers
      $ul = $('#search-results').empty();
      $sm = $('#search-matches').empty();
      // Search count indicator
      if (projects.length > 0) {
        $sm.html(
          '<span class="user-score">' + (projects.length) + '</span> ' +
          'projects match'
        );
      }
      // Create project cards
      projects.forEach(function(p) {
        $ul.append(
          '<a class="col col-2 col-sm-2 col-md-4 col-lg-4 ms-auto mr-1 card project" ' +
             'target="_blank" ' +
             'href="' + p.url + '"' +
             (p.image_url ?
               ' style="background-image:url(' + p.image_url + '); padding-left:100px"' : '') + '>' +
            '<div class="card-body">' +
              '<h5 class="card-title">' + p.name + '</h5>' +
              '<p class="card-text">' + p.summary + '</p>' +
            '</div>' +
          '</a>'
        );
      });
    }); //- get searchForm
  }

  function checkSearchQuery() {
    let paramString = (new URL(document.location)).searchParams;
    let searchParams = new URLSearchParams(paramString);
    if (searchParams.has("q")) {
      let q = searchParams.get("q");
      searchForm.find('input[name="q"]').val(q);
      runSearch(q);
    }
  }

  // Clickable categories navigation
  var $navCategories = $('.nav-categories .btn-group label').click(function(e) {
    $(this).parent().find('.active').removeClass('active');
    $(this).parent().addClass('active');
    var selected_id = $(this).find('input').attr('id');
    var $projects = $('.honeycomb .hexagon');
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

  // Show GitHub issues
  $('#issues-list').each(function() {
    var per_page = 5;
    var $self = $(this);
    var userAndRepo = $self.data('github');
    var url_api = 'https://api.github.com/repos/' + userAndRepo + '/issues';
    var url_www = 'https://github.com/' + userAndRepo + '/issues';
    $.getJSON(url_api + '?per_page=' + (per_page + 1), function(data) {
      $self.empty();
      $.each(data, function(index) {
        if (index == per_page) {
          return;
          // Show link to more issues:
          // return $self.append(
          //   '<a href="' + url_www +
          //   '" class="list-group-item link-more" target="_blank">All issues ...</a>'
          // );
        }
        $self.append(
          '<a href="' + this.html_url +
          '" class="list-group-item" target="_blank">' +
          '<img src="' + this.user.avatar_url + '">&nbsp;' + this.title + '</a>'
        );
      });
    });
  });

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

  // Admin event import
  // this is the id of the form
  $("#importEvent form").submit(function(e) {
    var $form = $(this);
    if ($form.find('input[type="file"]').val().length>0) return;
    e.preventDefault();
    var url = $form.attr('action');
    $form.find('input[type="submit"]').addClass('disabled');
    $form.find('.message-ok,.message-error').hide();
    $.ajax({
      type: "POST",
      url: url,
      data: $form.serialize(),
      success: function(data) {
        // Handle response
        console.log(data);
        if (data.status == 'Error') {
          $form.find('.message-error').html(data.errors.join('\n')).show();
        } else {
          $form.find('.message-ok').show();
        }
        $form.find('input[type="submit"]').removeClass('disabled');
      },
      error: function(err) {
        $form.find('input[type="submit"]').removeClass('disabled');
        console.error(err.statusText);
        $form.find('.message-error').show();
      }
    });
  });

  // Ye olde darke moude
  function setDarkMode(toggle) {
    dm = Boolean(window.darkmode);
    if (toggle) dm = !dm;
    if (dm) {
      // Invert page colors
      $('body').css('-webkit-filter','invert(100%)')
               .css('-moz-filter','invert(100%)')
               .css('-o-filter','invert(100%)')
               .css('-ms-filter','invert(100%)')
               .css('background', 'black')
               .css('height', '100%');
    } else {
      $('body').attr('style','');
      // Adjust clock theme
      // $('.flipdown').removeClass('flipdown__theme-dark').addClass('flipdown__theme-light');
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
