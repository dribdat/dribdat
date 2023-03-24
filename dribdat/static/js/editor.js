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
      // Clear template selection
      $('.template-select label input').prop('checked', false);
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
  }); // -autotext_url each

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

  // Push template selection to form
  $('.template-select label input').change(function() {
    $('input#template').val($(this).val());
    $('#autotext_url').val('');
  });




  // Upload images
  $('#uploadImage').each(function() {
    var $dialog = $(this);
    var $togglebtn = $('button[data-target="#uploadImage"]');
    // Enable the available fields
    var $longtext = $('.fld-longtext');
    if ($longtext.length > 0) {
      $longtext.prepend($togglebtn.clone().show());
    } else {
      $dialog.find("[data-target='pitch']").hide();
    }
    var $webpage_url = $('.fld-webpage_url');
    if ($webpage_url.length > 0) {
      $webpage_url.prepend($togglebtn.clone().show());
    } else {
      $dialog.find("[data-target='weblink']").hide();
    }
    var $imageurl = $('.fld-image_url,.fld-logo_url');
    if ($imageurl.length > 0) {
      // Image url field
      $imageurl.append($togglebtn.clone().show());
    } else {
      $dialog.find("[data-target='cover']").hide();
    }
    var $postnote = $('.fld-note');
    if ($postnote.length > 0 && $('body').hasClass('projectpost')) {
      // Post note
      $postnote.prev().prepend($togglebtn.clone().show());
    } else {
      $dialog.find("[data-target='post']").hide();
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
          $('#img-confirm').show().find('button').off("click").click(function() {
            if ($(this).data('target') == 'weblink') {
              // Replace the demo link
              $('#webpage_url').val(response);
              $('#is_webembed:not(:checked)').click();
              $dialog.modal('hide');
            } else if ($(this).data('target') == 'cover') {
              // Replace the cover
              $('#image_url,#logo_url').val(response);
              $dialog.modal('hide');
            } else if ($(this).data('target') == 'post') {
              // Append to post
              var imglink = '![](' + response + ')';
              $('#note').val(imglink + ' ' + $('#note').val());
              $dialog.modal('hide');
            } else if ($(this).data('target') == 'pitch') {
              // Append to pitch
              var imglink = '![ Title ](' + response + ')';
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
    $webpageurl.prepend($togglebtn.clone().show());
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
          // User confirms the file upload
          $('#file-confirm').show().find('button').off("click").click(function() {
            if ($(this).data('target') == 'weblink') {
              // Replace the cover
              $('#webpage_url').val(response);
              $('#is_webembed:not(:checked)').click();
              $dialog.modal('hide');
            } else if ($(this).data('target') == 'pitch') {
              // Determine file extension
              //var fileExt = filename.split('.');
              //fileExt = (fileExt.length > 1) ? fileExt[fileExt.length - 1] : '?';
                  // ... ' (' + fileExt.toUpperCase() + ')';
              // Create Markdown link with a paperclip emoji
              var fileLink = '📎 [' + filename + '](' + response + ')'; 
              // Append to pitch
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
  }); // -#uploadImage Files




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
  }); // -importEvent form

  // Initialize rich editor for Markdown
  function activate_editor() {
    if (typeof toastui !== 'object') return;
    const $longtext = $('#longtext');
    if (!$longtext.length) return;
    $longtext.after('<div id="mdeditor" style="text-align:left"></div>');

    const toasteditor = window.toasteditor = new toastui.Editor({
      el: document.querySelector('#mdeditor'),
      previewStyle: 'tab', height: '500px',
      initialValue: $longtext.hide().text(),
      usageStatistics: false,
      toolbarItems: [
        ['heading', 'bold', 'italic'],
        ['hr', 'quote', 'strike'],
        ['ul', 'ol'],
        ['table', 'link'],
        ['code', 'codeblock'],
      ]
    });

    // Handle form submission
    $longtext.parents('form').submit(function() {
      $longtext.val(toasteditor.getMarkdown());
    });

    // Save settings
    localStorage.setItem('markdownhelper', '1');
    const $activateEditor = $('#activateEditor');
    $activateEditor.find('[data-do="activate"]').hide();
    $activateEditor.find('[data-do="reset"]').show().click(function() {
        if (window.confirm('Save changes first! Continue?')) {
          localStorage.setItem('markdownhelper', '0');
          window.location.reload();
        }
      });

    console.info('editor ready.');
  }

  // Characters remaining, thanks to James Bruton
  function markRequired() {
    var control = $(this).find(".form-control");
    var label = $(this).children("label");
    if (control.attr("required") == "required") {
        label.addClass("required");
    }
  }
  function countCharacters() {
      var max = $(this).attr("maxlength");
      if (!max) return;
      var length = $(this).val().length;
      var counter = max - length;
      var helper = $(this).next().find(".form-text");
      helper = helper.length ? helper :
        $(this).next().append("<span class='form-text'></span>").find(".form-text");
      // Switch to the singular if there's exactly 1 character remaining
      if (counter !== 1) {
          helper.text(counter + " characters remaining");
      } else {
          helper.text(counter + " character remaining");
      }
      // Make it red if there are 0 characters remaining
      if (counter === 0) {
          helper.removeClass("text-muted");
          helper.addClass("text-danger");
      } else {
          helper.removeClass("text-danger");
          helper.addClass("text-muted");
      }
  }

  function init_forms() {
      $(".form-group").each(markRequired);
      $(".form-control").each(countCharacters);
      $(".form-control").keyup(countCharacters);
  }

  function init_editor() {
    const $activateEditor = $('#activateEditor');
    const $longtext = $('#longtext');

    // Move button to editing area
    $longtext.first().before($activateEditor);

    // Handle activation button
    $activateEditor.find('[data-do="activate"]')
                   .show().on('click', activate_editor);

    // Enable by default
    if (localStorage.getItem('markdownhelper') === null) {
      localStorage.setItem('markdownhelper', '1');
    }

    // Load settings
    if (localStorage.getItem('markdownhelper') == '1') {
      setTimeout(activate_editor, 100);
    }
  } //- init_editor

  // Bootup
  init_editor();
  init_forms();

}).call(this, jQuery, window);
