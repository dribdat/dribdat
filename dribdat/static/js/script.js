(function($, window) {

  // Open up the LOG if navigated
  if (window.location.hash == '#log' || window.location.pathname.endsWith('/log')) {
    $('#dribs-tab-md').click();
  }

  // Ajaxify dribs pagination
  $('#next-dribs').click(function(e) {
    e.preventDefault(); e.stopPropagation();
    var $self = $(this);
    if ($self.hasClass('disabled')) return;
    $self.addClass('disabled'); // while loading / finished
    $.get($self.attr('href'), function(d) {
      $('section.timeline').append($(d).find('section.timeline').html());
      $next = $(d).find('#next-dribs');
      if ($next.length) {
        $self.removeClass('disabled').attr('href', $next.attr('href'));
      } else {
        $self.removeClass('btn-primary').html('BOF');
      }
    });
  })

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
          'projects match' +
          (projects.length > 3 ? '&nbsp;&#9654;&#9654;' : '')
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
  } // -runSearch

  // Runs an inline search based on the document URL
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
  }); // -navCategories

  // Toggle challenges after the hackathon
  // $('.event-finished .nav-categories #challenges').parent().click();

  // Enable tooltips on hexagrid
  $('.honeycomb .hexagon[data-toggle="tooltip"]').tooltip();

  // Roll up categories if there is only one, and no projects
  if ($navCategories.length === 1) {
    $navCategories.click().parent().parent().hide();
  }

  // Show embed code when button clicked
  $('#embed-link').click(function(e) {
    e.preventDefault(); e.stopPropagation();
    var url = $(this).attr('href') + '?embed=1';
    var code = '<iframe src="' + url + '" style="width:100%;height:320px;background:transparent;border:none;overflow:hidden" scrolling="no"></iframe>';
    window.prompt('Share the event link in social media, or copy and paste this HTML code to embed on your site. For even better embedding, visit github.com/dribdat/backboard', code);
  });

  // Horizontal desktop dragging of project pages
  $('.profile-projects .row').each(function() {
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
  }); // -profile-projects row

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
  }); // -issues-list

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
      $('footer .darkmode span').html('Light');
    } else {
      $('body').attr('style','');
      $('footer .darkmode span').html('Dark');
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
  }); //-darkmode

  function init_clock() {
    // Initialise home page countdown
    $('.event-countdown').each(function() {
      var startdate = $(this).data('start');
      var datenow = Date.now();
      var datesched = Date.parse(startdate.replace(' ', 'T'));
      var timeleft = datesched - datenow;
      if (isNaN(timeleft) || timeleft < 0) return;
      var unixtime = datesched / 1000;
      // Start the clock
      new FlipDown(unixtime, $(this).attr('id')).start();
    });

    // Initialise carousel
    $('.carousel').carousel();
  }


  // Bootup
  init_clock();
  checkSearchQuery();

  console.info('dribdat ready.');

}).call(this, jQuery, window);
