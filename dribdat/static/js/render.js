(function($, window) {

let $thebody = $('body');
let $thecanvas = $('#canv');
let url = $thebody.attr('src');
let pdfjsLib = window["pdfjs-dist/build/pdf"];

pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

let pdfDoc = null,
    pageNum = 1,
    scale = 1,
    pageRendering = false,
    pageNumPending = null,
    canvas = $thecanvas[0],
    ctx = canvas.getContext('2d');

const DEFAULT_SCALE_DELTA = 1.1,
      MIN_SCALE = 0.25,
      MAX_SCALE = 5.0;

/*
// Support HiDPI-screens and fit to full screen mode

    var outputScale = window.devicePixelRatio || 1;

    canvas.width = Math.floor(viewport.width * outputScale);
    canvas.height = Math.floor(viewport.height * outputScale);
    canvas.style.width = Math.floor(viewport.width) + "px";
    canvas.style.height =  Math.floor(viewport.height) + "px";

    var transform = outputScale !== 1
      ? [outputScale, 0, 0, outputScale, 0, 0]
      : null;

    // Render PDF page into canvas context
    var renderContext = {
      canvasContext: ctx,
      transform: transform,
      viewport: viewport
    };
*/

/**
 * Get page info from document, resize canvas accordingly, and render page.
 * @param num Page number.
 */
function renderPage(num) {
  pageRendering = true;
  // Using promise to fetch the page
  pdfDoc.getPage(num).then(function(page) {
    var viewport = page.getViewport({scale: 1.5});
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    var transform = scale !== 1
      ? [scale, 0, 0, scale, 0, 0]
      : null;

    // Render PDF page into canvas context
    var renderContext = {
      canvasContext: ctx,
      transform: transform,
      viewport: viewport
    };
    var renderTask = page.render(renderContext);

    // Wait for rendering to finish
    renderTask.promise.then(function() {
      pageRendering = false;
      if (pageNumPending !== null) {
        // New page rendering is pending
        renderPage(pageNumPending);
        pageNumPending = null;
      }
    });
  });

  // Update page counters
  document.getElementById('page_num').textContent = num;
}

/**
 * If another page rendering in progress, waits until the rendering is
 * finised. Otherwise, executes rendering immediately.
 */
function queueRenderPage(num) {
  if (pageRendering) {
    pageNumPending = num;
  } else {
    renderPage(num);
  }
}

/**
 * Displays previous page.
 */
function onPrevPage() {
  if (pageNum <= 1) {
    return;
  }
  pageNum--;
  queueRenderPage(pageNum);
}
document.getElementById('prev').addEventListener('click', onPrevPage);

/**
 * Displays next page.
 */
function onNextPage() {
  if (pageNum >= pdfDoc.numPages) {
    return;
  }
  pageNum++;
  queueRenderPage(pageNum);
}
document.getElementById('next').addEventListener('click', onNextPage);

// Keyboard navigation
$("body").keydown(function(e) {
  //console.log(e.keyCode);
  if (e.keyCode == 37) { // left
    onPrevPage();
  }
  else if(e.keyCode == 39) { // right
    onNextPage();
  }
  else if(e.keyCode == 33) { // page up
    onPrevPage();
  }
  else if(e.keyCode == 34) { // page down
    onNextPage();
  }
  else if(e.keyCode == 32) { // spacebar
    onNextPage();
  }
});

/**
 * Goes to some page.
 */
function onGoPage() {
  let pageNum = Number.parseInt(window.prompt());
  if (!Number.isInteger(pageNum)) return;
  pageNum = (pageNum < 1) ? 1 : (pageNum > pdfDoc.numPages) ? pdfDoc.numPages : pageNum;
  queueRenderPage(pageNum);
}
document.getElementById('go').addEventListener('click', onGoPage);

/**
 * Twists the lens.
 */
function pdfViewZoomIn(ticks) {
  let newScale = scale;
  do {
    newScale = (newScale * DEFAULT_SCALE_DELTA).toFixed(2);
    newScale = Math.ceil(newScale * 10) / 10;
    newScale = Math.min(MAX_SCALE, newScale);
  } while (--ticks && newScale < MAX_SCALE);
  scale = newScale;
  console.log(scale);
  renderPage(pageNum);
}
document.getElementById('zoomIn').addEventListener('click', pdfViewZoomIn);

function pdfViewZoomOut(ticks) {
  let newScale = scale;
  do {
    newScale = (newScale / DEFAULT_SCALE_DELTA).toFixed(2);
    newScale = Math.floor(newScale * 10) / 10;
    newScale = Math.max(MIN_SCALE, newScale);
  } while (--ticks && newScale > MIN_SCALE);
  scale = newScale;
  console.log(scale);
  renderPage(pageNum);
}
document.getElementById('zoomOut').addEventListener('click', pdfViewZoomOut);

/**
 * Asynchronously downloads PDF.
 */
pdfjsLib.getDocument(url).promise.then(function(pdfDoc_) {
  pdfDoc = pdfDoc_;
  document.getElementById('page_count').textContent = pdfDoc.numPages;

  // Initial/first page rendering
  renderPage(pageNum);
  
  // Hide buttons if one pager
  if (pdfDoc.numPages < 2) {
    $('.btn-group').hide();
  }
});


}).call(this, jQuery, window);
