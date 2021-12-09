// Initialize rich editor for Markdown
$('#longtext').each(function() {
  if (typeof toastui !== 'object') return;
  const $mdsource = $(this);
  $mdsource.after('<div id="mdeditor" style="text-align:left"></div>');
  const toasteditor = window.toasteditor = new toastui.Editor({
    el: document.querySelector('#mdeditor'),
    previewStyle: 'tab', height: '500px',
    initialValue: $mdsource.hide().text(),
    usageStatistics: false,
    toolbarItems: [
      ['heading', 'bold', 'italic'],
      ['hr', 'quote', 'strike'],
      ['ul', 'ol'],
      ['table', 'link'],
      ['code', 'codeblock'],
    ]
  });
  $mdsource.parents('form').submit(function() {
    $mdsource.val(toasteditor.getMarkdown());
  });
});
