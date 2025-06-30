(function ($, window) {
  // Initialize project data loader
  $("#autotext_url").each(function () {
    // Check if the URL is compliant
    var checkAutotext = function (val, $ind) {
      if (typeof val !== "string") return;
      if (val.trim() === "") return;
      $ind
        .find("i")
        .removeClass("fa-circle-o fa-check-circle-o")
        .addClass("fa-circle-o")
        .css("color", "red");
      $("#is_autoupdate").click(function () {
        if ($(this).is(":checked"))
          if (!$indicator.find("button").click()) $(this).click();
      });
    };
    // Toggle status indicator
    var $inputfield = $(this);
    var $indicator = $inputfield
      .parent()
      .prepend(
        '<span class="autotext-indicator float-right">' +
          '<a title="Status" class="btn-disabled me-1"><i class="fa fa-circle-o"></i></a>' +
          '<button class="btn btn-light" type="button">Test</button>' +
          "</span>",
      )
      .find(".autotext-indicator");
    var $inputbutton = $indicator.find("button");

    // Get remote data
    var runAutofill = function ($button, url) {
      // Put UI in waiting mode
      $indicator.find("i").css("color", "blue");
      $button.attr("disabled", "disabled").html("Please wait ...");
      // Call updater API
      $.getJSON("/api/project/autofill?url=" + url, function (data) {
        $button.removeAttr("disabled");
        if (!data || typeof data.name === "undefined" || data.name === "") {
          $("div.import-note").removeClass('hidden');
          $("#is_autoupdate").prop("checked", false);
          $indicator.find("i").css("color", "red");
          $button.html("Retry");
          return;
        }
        $button.html("Ready");
        $indicator.find("i")
          .removeClass("fa-circle-o fa-check-circle-o")
          .addClass("fa-check-circle-o")
          .css("color", "green");
        // Set form values
        if (!$("input#name").val()) $("input#name").val(data.name);
        if (!$("input#summary").val()) $("input#summary").val(data.summary);
        if (!$("input#webpage_url").val())
          $("input#webpage_url").val(data.webpage_url);
        if (!$("input#source_url").val())
          $("input#source_url").val(data.source_url);
        if (!$("input#contact_url").val())
          $("input#contact_url").val(data.contact_url);
        if (!$("input#download_url").val())
          $("input#download_url").val(data.download_url);
        if (!$("input#image_url").val())
          $("input#image_url").val(data.image_url);
        // Allow submitting form
        $("#submit").removeAttr("disabled");
      }).fail(function () {
        window.alert(
          "Could not connect to remote site - please try again later",
        );
        $button.removeAttr("disabled").html("Retry");
      });
    }; // -runAutofill

    // On load
    checkAutotext($inputfield.val(), $indicator);

    // On keypress
    $inputfield.on("keyup", function (e) {
      checkAutotext($inputfield.val(), $indicator);
      // Clear template selection
      $(".template-select label input").prop("checked", false);
    });

    // On change
    const ms_timeout = 1000;
    $inputfield.on("input", function (e) {
      e.preventDefault(); e.stopPropagation();
      $inputfield.data('updated', new Date().getTime());
      setTimeout(() => { 
        if (new Date().getTime() - ms_timeout >= $inputfield.data('updated')) {
          var url = $inputfield.val();
          runAutofill($inputbutton, url);
        }
      }, ms_timeout);
    });

    // Update button
    $inputbutton.click(function (e) {
      e.preventDefault(); e.stopPropagation();
      var url = $inputfield.val();
      runAutofill($inputbutton, url);
    });
  }); // -autotext_url each

  // Allow project progress on acknowledge
  if ($(".projectpost .stage-conditions .stage-no").length == 0) {
    $('.form-project-post label[for="has_progress"] input').attr('checked', true);
  } else {
    $('.form-project-post label[for="has_progress"]').parent().hide();
  }

  // Make the custom color field HTML5 compatible
  $("input#logo_color[type=text]").attr("type", "color");

  // Open up the README on click
  $(".project-autotext").click(function () {
    $(this).addClass("active");
  });

  // Push template selection to form
  $(".template-select label input").change(function () {
    $("input#template").val($(this).val());
    $("#autotext_url").val("");
  });

  // Upload images
  $("#uploadImage").each(function () {
    var $dialog = $(this);
    var $togglebtn = $('button[data-bs-target="#uploadImage"]');
    // Enable the available fields
    var $longtext = $(".fld-longtext");
    if ($longtext.length > 0) {
      $longtext.prepend($togglebtn.clone().show());
    } else {
      $dialog.find("[data-target='pitch']").hide();
    }
    var $imageurl = $(".fld-image_url,.fld-logo_url");
    if ($imageurl.length > 0) {
      // Image url field
      $imageurl.append($togglebtn.clone().show());
    } else {
      $dialog.find("[data-target='cover']").hide();
    }
    var $postnote = $(".fld-note");
    if ($postnote.length > 0 && $("body").hasClass("projectpost")) {
      // Post note
      $postnote.prev().prepend($togglebtn.clone().show());
    } else {
      $dialog.find("[data-target='post']").hide();
    }
    // Set up the file dialog
    var $inputfd = $dialog.find('input[type="file"]');
    $inputfd.change(function () {
      var imgfile = $inputfd[0].files[0];
      // Check file size limits
      var maxsize = parseInt($inputfd.data("maxsize"));
      if (imgfile.size > maxsize) {
        return alert(
          "Please upload a smaller file (reduce resolution, save as JPEG)",
        );
      }
      // Create upload object
      var fdd = new FormData();
      fdd.append("file", imgfile);
      $.ajax({
        url: "/api/project/uploader",
        type: "post",
        data: fdd,
        processData: false,
        contentType: false,
        success: function (response) {
          if (response.indexOf("http") !== 0) {
            return alert("File could not be uploaded :(\n" + response);
          }
          $dialog.find(".preview img").attr("src", response);
          $dialog.find(".preview input").val(response);
          $dialog.find(".hidden").show();
          $("#img-confirm")
            .show()
            .find("button")
            .off("click")
            .click(function () {
              if ($(this).data("target") == "cover") {
                // Replace the cover
                $("#image_url,#logo_url").val(response);
                $dialog.modal("hide");
              } else if ($(this).data("target") == "post") {
                // Append to post
                var imglink = "![](" + response + ")";
                if (typeof window.Editor !== "undefined") {
                  // As an image
                  window.Editor.codemirror.replaceRange(imglink, {line: Infinity});
                } else {
                  $("#note").val(imglink + " " + $("#note").val());
                }
                $dialog.modal("hide");
              } else if ($(this).data("target") == "pitch") {
                // Generate a cleaner filename
                var filename = response
                  .split(/(\\|\/)/g).pop()
                  .replaceAll("_", " ");
                var imglink = "![" + filename + "](" + response + ")";
                if (typeof window.Editor !== "undefined") {
                  // As an image
                  window.Editor.codemirror.replaceRange(imglink, {line: Infinity});
                } else {
                  // Append to pitch
                  $("#longtext").val($("#longtext").val() + "\n\n" + imglink);
                }
                $dialog.modal("hide");
              } else {
                // Copy to clipboard
                if (navigator.clipboard) {
                  navigator.clipboard.writeText(response);
                  $dialog.modal("hide");
                } else {
                  $dialog.find(".preview input").click().select();
                  document.execCommand("copy");
                }
              }
            });
        },
        error: function (e) {
          alert("Sorry, an error has occurred.\n" + e.statusText);
        },
      }); // -ajax
    }); // -change
  }); // -#uploadImage

  // Upload a presentation file
  $("#uploadFile").each(function () {
    var $dialog = $(this);
    var $togglebtn = $('button[data-bs-target="#uploadFile"]');
    // Enable the available fields
    var $webpageurl = $(".fld-webpage_url");
    // Append button to the editor
    $webpageurl.prepend($togglebtn.clone().show());
    // Set up the file dialog
    var $inputfd = $dialog.find('input[type="file"]');
    $inputfd.change(function () {
      var thefile = $inputfd[0].files[0];
      // Check file size limits
      var maxsize = parseInt($inputfd.data("maxsize"));
      if (thefile.size > maxsize) {
        return alert("Please upload a smaller file (1 MB limit)");
      }
      // Create upload object
      var fdd = new FormData();
      fdd.append("file", thefile);
      $.ajax({
        url: "/api/project/uploader",
        type: "post",
        data: fdd,
        processData: false,
        contentType: false,
        success: function (response) {
          if (response.indexOf("http") !== 0) {
            return alert("File could not be uploaded :(\n" + response);
          }
          // Parse the file name and size
          var filename = response
            .split(/(\\|\/)/g)
            .pop()
            .replaceAll("_", " ");
          var fileext = filename.split(".").pop().toLowerCase();
          var filesize = Math.round(thefile.size / 102.4) / 10;
          filesize =
            filesize > 1000
              ? Math.round(filesize / 102.4) / 10 + " MB"
              : filesize + " KB";

          // Get the form ready
          $dialog.find(".preview input").val(response);
          $dialog.find(".hidden").removeClass("hidden");

          // Preview values
          $dialog.find(".file-preview").removeClass("hidden");
          $dialog.find(".file-preview .filename").html(filename);
          $dialog.find(".file-preview .filesize").html(filesize);
          $dialog.find(".file-preview .filetype *").addClass("hidden");

          // Special file types
          if (filename.indexOf("datapackage.json") > 0) {
            $dialog
              .find(".file-preview .filetype-frictionless")
              .removeClass("hidden");
          } else {
            $dialog
              .find(".file-preview .filetype-" + fileext)
              .removeClass("hidden");
          }

          // User confirms the file upload
          $("#file-confirm")
            .show()
            .find("button")
            .off("click")
            .click(function () {
              if ($(this).data("target") == "weblink") {
                // Replace the cover
                $("#webpage_url").val(response);
                $("#is_webembed:not(:checked)").click();
                $dialog.modal("hide");
              } else {
                // Copy to clipboard
                if (navigator.clipboard) {
                  navigator.clipboard.writeText(response);
                  $dialog.modal("hide");
                } else {
                  $dialog.find(".preview input").click().select();
                  document.execCommand("copy");
                }
              }
            });
        },
        error: function (e) {
          alert("Sorry, an error has occurred.\n" + e.statusText);
        },
      }); // -ajax
    }); // -change
  }); // -#uploadFile

  // Upload a dataset file
  $("#uploadPackage").each(function () {
    var $dialog = $(this);
    var $togglebtn = $('button[data-bs-target="#uploadPackage"]');
    // Enable the available fields
    var $longtext = $(".fld-longtext");
    // Append button to the pitch editor
    $longtext.prepend($togglebtn.clone().show());
    // Set up the file dialog
    var $inputfd = $dialog.find('input[type="file"]');
    $inputfd.change(function () {
      var thefile = $inputfd[0].files[0];
      // Check file size limits
      var maxsize = parseInt($inputfd.data("maxsize"));
      if (thefile.size > maxsize) {
        return alert("Please upload a smaller file (1 MB limit)");
      }
      // Create upload object
      var fdd = new FormData();
      fdd.append("file", thefile);
      $.ajax({
        url: "/api/project/uploader",
        type: "post",
        data: fdd,
        processData: false,
        contentType: false,
        success: function (response) {
          if (response.indexOf("http") !== 0) {
            return alert("File could not be uploaded :(\n" + response);
          }
          // Parse the file name and size
          var filename = response
            .split(/(\\|\/)/g)
            .pop()
            .replaceAll("_", " ");
          var fileext = filename.split(".").pop().toLowerCase();
          var filesize = Math.round(thefile.size / 102.4) / 10;
          filesize =
            filesize > 1000
              ? Math.round(filesize / 102.4) / 10 + " MB"
              : filesize + " KB";

          // Get the form ready
          $dialog.find(".preview input").val(response);
          $dialog.find(".hidden").removeClass("hidden");

          // Preview values
          $dialog.find(".file-preview").removeClass("hidden");
          $dialog.find(".file-preview .filename").html(filename);
          $dialog.find(".file-preview .filesize").html(filesize);
          $dialog.find(".file-preview .filetype *").addClass("hidden");

          // Special file types
          const isDataPackage = filename.indexOf("datapackage.json") >= 0;
          if (isDataPackage) {
            $dialog
              .find(".file-preview .filetype-frictionless")
              .removeClass("hidden");
          } else {
            $dialog
              .find(".file-preview .filetype-" + fileext)
              .removeClass("hidden");
          }

          // User confirms the file upload
          $("#data-confirm")
            .show()
            .find("button")
            .off("click")
            .click(function () {
              if ($(this).data("target") == "pitch") {
                // Determine file extension
                //var fileExt = filename.split('.');
                //fileExt = (fileExt.length > 1) ? fileExt[fileExt.length - 1] : '?';
                // ... ' (' + fileExt.toUpperCase() + ')';
                // Append to pitch
                if (typeof window.Editor !== "undefined") {
                  if (isDataPackage) {
                    window.Editor.codemirror.replaceRange(response, {line: Infinity});
                  } else {
                    var linkmd = '[' + filename + '](' + response + ')';
                    window.Editor.codemirror.replaceRange(linkmd, {line: Infinity});
                  }
                } else {
                  // Create Markdown link with a paperclip emoji
                  var fileLink = "📎 [" + filename + "](" + response + ")";
                  if (isDataPackage) {
                    fileLink = response;
                  }
                  $("#longtext").val($("#longtext").val() + "\n\n" + fileLink);
                }
                $dialog.modal("hide");
              } else {
                // Copy to clipboard
                if (navigator.clipboard) {
                  navigator.clipboard.writeText(response);
                  $dialog.modal("hide");
                } else {
                  $dialog.find(".preview input").click().select();
                  document.execCommand("copy");
                }
              }
            });
        },
        error: function (e) {
          alert("Sorry, an error has occurred.\n" + e.statusText);
        },
      }); // -ajax
    }); // -change
  }); // -#uploadPackage

  // Media upload
  $("#uploadMedia").each(function () {
    var $dialog = $(this);
    var $togglebtn = $('button[data-bs-target="#uploadMedia"]');
    // Append button to the pitch editor
    var $longtext = $(".fld-longtext");
    $longtext.prepend($togglebtn.clone().show());
    // Set up the dialog
    var $inputfd = $dialog.find('input[type="url"]');
    var $submitb = $dialog.find('button[data-target="insert"');
    $submitb.click(function () {
      var theurl = $inputfd.val();
      if (theurl.indexOf("https://") !== 0) {
        return window.alert("Invalid address");
      }
      // Add some spaces
      theurl = "\n" + theurl + "\n";
      // Append to pitch
      if (typeof window.Editor !== "undefined") {
        window.Editor.codemirror.replaceRange(theurl, {line: Infinity});
      } else {
        theurl = "\n" + theurl + "\n"; // More spaces
        $("#longtext").val($("#longtext").val() + theurl);
      }
      $dialog.modal("hide");
    });
  }); // -#uploadMedia

  // Tool suggestions
  $("#suggestTool").each(function () {
    var $dialog = $(this);
    var $togglebtn = $('button[data-bs-target="#suggestTool"]');
    // Append button to the pitch editor
    var $targetfld = $(".fld-webpage_url");
    $targetfld.prepend($togglebtn.clone().show());
    // Set up the dialog
    var $inputfd = $dialog.find('input[type="url"]');
    var $submitb = $dialog.find('button[data-target="insert"');
    $submitb.click(function () {
      var theurl = $inputfd.val();
      if (theurl.indexOf("https://") !== 0) {
        return window.alert("Invalid address");
      }
      // Replace url
      $("input", $targetfld).val(theurl);
      $dialog.modal("hide");
    });
  }); // -#uploadMedia

  // Admin button tips
  $(".admin-defaults button").click(function () {
    $("input#name").val($(this).text());
  });

  // Admin event import
  // this is the id of the form
  $("#importEvent form").submit(function (e) {
    var $form = $(this);
    if ($form.find('input[type="file"]').val().length > 0) return;
    e.preventDefault();
    var url = $form.attr("action");
    $form.find('input[type="submit"]').addClass("disabled");
    $form.find(".message-ok,.message-error,.buttons").hide();
    $form.find(".message-loading").show();
    $.ajax({
      type: "POST",
      url: url,
      data: $form.serialize(),
      success: function (data) {
        // Handle response
        //console.log(data);
        $form.find(".buttons").show();
        $form.find(".message-loading").hide();
        if (data.status == "Error") {
          $form.find(".message-error").html(data.errors.join("\n")).show();
        } else {
          $form.find(".message-ok").show();
        }
        $form.find('input[type="submit"]').removeClass("disabled");
      },
      error: function (err) {
        $form.find('input[type="submit"]').removeClass("disabled");
        console.error(err.statusText);
        $form.find(".buttons").show();
        $form.find(".message-error").show();
      },
    });
  }); // -importEvent form

  // Initialize rich editor for Markdown
  function activate_editor() {
    if (typeof EasyMDE !== "function") return;
    const $longtext = $("#longtext,#note").first();
    if (!$longtext.length) return;
    const is_note = $longtext.attr('id') == 'note';

    // Handle form submission
    $longtext.parents("form").submit(function () {
      $('#submit', this).addClass('disabled')
        .attr('disabled', 'disabled');
    });

    // Configure the WYSIWYG mode
    const Editor = new EasyMDE({
      element: $longtext[0],
      autofocus: is_note,
      minHeight: is_note ? "100px" : "500px",
      spellChecker: false,
      sideBySideFullscreen: false
    });

    // Save settings
    localStorage.setItem("markdownhelper", "1");
    const $activateEditor = $("#activateEditor");
    $activateEditor.find('[data-do="activate"]').hide();
    $activateEditor
      .find('[data-do="reset"]')
      .show()
      .click(function () {
        if (window.confirm("Save changes first! Continue?")) {
          localStorage.setItem("markdownhelper", "0");
          window.location.reload();
        }
      });

    window.Editor = Editor;
    console.info("editor ready.");
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
    // Ignore for big fields
    if (!max || max > 1000) return;
    var length = $(this).val().length;
    var counter = max - length;
    var helper = $(this).next().find(".form-text");
    helper = helper.length
      ? helper
      : $(this)
          .next()
          .append("<span class='form-text'></span>")
          .find(".form-text");
    // Switch to the singular if there's exactly 1 character remaining
    if (counter !== 1) {
      helper.text(counter + " bytes");
    } else {
      helper.text("All out of bytes!");
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
    const $activateEditor = $("#activateEditor");

    // Handle activation button
    $activateEditor
      .find('[data-do="activate"]')
      .show()
      .on("click", activate_editor);

    // Enable by default
    if (localStorage.getItem("markdownhelper") === null) {
      localStorage.setItem("markdownhelper", "1");
    }

    // Load settings
    if (localStorage.getItem("markdownhelper") == "1") {
      setTimeout(activate_editor, 100);
    }
  } //- init_editor

  // Bootup
  init_editor();
  init_forms();
}).call(this, jQuery, window);
