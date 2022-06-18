const $activateEditor = $('#activateEditor');
const $longtext = $('#longtext');

// Move button to editing area
$longtext.first().each(function() {
  $(this).before($activateEditor);
});

// Handle button
$activateEditor.show().on('click', function() {
  if (typeof toastui !== 'object') return;
  $longtext.after('<div id="mdeditor" style="text-align:left"></div>');

  // Initialize rich editor for Markdown
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
  $(this).hide();
});
