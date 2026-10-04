// visualexplain canvas shell. Linked by every generated page; see SKILL.md.
//
// Moves and scales #ve-world as one piece (pan, zoom, fit, jump to a frame) and
// renders `pre.mermaid` blocks. Classic script on purpose: a module does not load
// from file://.
(function () {
  'use strict';

  var world = document.getElementById('ve-world');
  if (!world) throw new Error('visualexplain: the page has no #ve-world element');

  var MIN_SCALE = 0.05, MAX_SCALE = 8, MARGIN = 40;
  // Mermaid: the repo's cached copy first (bin/visualexplain mermaid-cache puts it
  // in tmp/visualexplain/, one level up from the page's folder), then the CDN.
  var MERMAID_SOURCES = [
    '../visualexplain/mermaid.min.js',
    'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js'
  ];

  var scale = 1, tx = 0, ty = 0;
  var frames = Array.prototype.slice.call(world.querySelectorAll('.ve-frame'));

  // ---- size freehand SVGs ---------------------------------------------------
  // An inline svg with only a viewBox has no size of its own inside a max-content
  // grid column. Give it its viewBox size in world pixels.
  function sizeSvgs() {
    world.querySelectorAll('.ve-frame svg').forEach(function (svg) {
      if (!svg.hasAttribute('viewBox') || svg.hasAttribute('width')) return;
      var vb = svg.viewBox.baseVal;
      svg.setAttribute('width', vb.width);
      svg.setAttribute('height', vb.height);
    });
  }

  // ---- shared arrowheads ----------------------------------------------------
  // marker-end="url(#ve-arrowhead)" on any freehand connector, or
  // #ve-arrowhead-added / -removed / -changed / -existing for a status colour.
  function addArrowheads() {
    var markers = ['', 'existing', 'added', 'removed', 'changed'].map(function (name) {
      var id = 've-arrowhead' + (name ? '-' + name : '');
      var colour = 'var(--ve-' + (name || 'muted') + ')';
      return '<marker id="' + id + '" viewBox="0 0 10 10" refX="9" refY="5" ' +
        'markerWidth="9" markerHeight="9" orient="auto-start-reverse" markerUnits="userSpaceOnUse">' +
        '<path d="M0,0 L10,5 L0,10 z" style="fill:' + colour + ';stroke:none"/></marker>';
    }).join('');
    var holder = document.createElement('div');
    holder.innerHTML = '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>' +
      markers + '</defs></svg>';
    document.body.appendChild(holder.firstChild);
  }

  // ---- HUD ------------------------------------------------------------------
  var hud = document.createElement('div');
  hud.id = 've-hud';
  document.body.appendChild(hud);

  function apply() {
    world.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')';
    hud.textContent = Math.round(scale * 100) + '%  ·  drag or scroll: pan  ·  pinch or ⌘/Ctrl + scroll: zoom  ·  0: fit  ·  1-9: frame';
  }

  // ---- view -----------------------------------------------------------------
  function clampScale(s) { return Math.min(MAX_SCALE, Math.max(MIN_SCALE, s)); }

  function zoomAt(cx, cy, factor) {
    var next = clampScale(scale * factor);
    tx = cx - (cx - tx) * (next / scale);
    ty = cy - (cy - ty) * (next / scale);
    scale = next;
    apply();
  }

  // Shows the world rectangle (x, y, w, h) centred, as large as fits, at most maxScale.
  function show(x, y, w, h, maxScale) {
    var vw = window.innerWidth, vh = window.innerHeight;
    scale = clampScale(Math.min((vw - 2 * MARGIN) / w, (vh - 2 * MARGIN) / h, maxScale));
    tx = (vw - w * scale) / 2 - x * scale;
    ty = (vh - h * scale) / 2 - y * scale;
    apply();
  }

  function fitAll() { show(0, 0, world.offsetWidth, world.offsetHeight, 1); }

  function showFrame(frame) {
    show(frame.offsetLeft, frame.offsetTop, frame.offsetWidth, frame.offsetHeight, 2);
  }

  // ---- pan by drag ----------------------------------------------------------
  var NO_DRAG = 'button, a, input, select, textarea, label, summary, [data-ve-nodrag]';
  var drag = null;

  document.addEventListener('pointerdown', function (e) {
    if (e.button !== 0 || e.target.closest(NO_DRAG)) return;
    drag = { x: e.clientX, y: e.clientY, tx: tx, ty: ty };
    document.body.classList.add('ve-dragging');
  });
  document.addEventListener('pointermove', function (e) {
    if (!drag) return;
    if (e.buttons === 0) return endDrag();  // the button went up outside the window
    tx = drag.tx + (e.clientX - drag.x);
    ty = drag.ty + (e.clientY - drag.y);
    apply();
  });
  function endDrag() {
    drag = null;
    document.body.classList.remove('ve-dragging');
  }
  document.addEventListener('pointerup', endDrag);
  document.addEventListener('pointercancel', endDrag);

  // ---- wheel: pan, or zoom with Cmd/Ctrl (a trackpad pinch arrives as Ctrl+wheel)
  document.addEventListener('wheel', function (e) {
    e.preventDefault();
    if (e.ctrlKey || e.metaKey) {
      var dy = Math.max(-60, Math.min(60, e.deltaY));
      zoomAt(e.clientX, e.clientY, Math.exp(-dy * 0.006));
      return;
    }
    var dx = e.deltaX, dyPan = e.deltaY;
    if (e.shiftKey && dx === 0) { dx = dyPan; dyPan = 0; }
    tx -= dx;
    ty -= dyPan;
    apply();
  }, { passive: false });

  // Safari reports a pinch as gesture events, not as Ctrl+wheel.
  var gestureScale = 1;
  document.addEventListener('gesturestart', function (e) { e.preventDefault(); gestureScale = 1; });
  document.addEventListener('gesturechange', function (e) {
    e.preventDefault();
    zoomAt(e.clientX, e.clientY, e.scale / gestureScale);
    gestureScale = e.scale;
  });

  // ---- keys -----------------------------------------------------------------
  document.addEventListener('keydown', function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.target.closest('input, textarea, select')) return;
    var k = e.key;
    if (k === '0' || k === 'f') fitAll();
    else if (/^[1-9]$/.test(k)) { if (frames[k - 1]) showFrame(frames[k - 1]); }
    else if (k === '+' || k === '=') zoomAt(window.innerWidth / 2, window.innerHeight / 2, 1.25);
    else if (k === '-') zoomAt(window.innerWidth / 2, window.innerHeight / 2, 0.8);
    else if (k === 'ArrowLeft') { tx += 80; apply(); }
    else if (k === 'ArrowRight') { tx -= 80; apply(); }
    else if (k === 'ArrowUp') { ty += 80; apply(); }
    else if (k === 'ArrowDown') { ty -= 80; apply(); }
    else return;
    e.preventDefault();
  });

  world.addEventListener('dblclick', function (e) {
    var title = e.target.closest('.ve-frame > h2');
    if (title) showFrame(title.parentElement);
  });

  // ---- Mermaid --------------------------------------------------------------
  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  // The status classes for flowcharts and state diagrams (`A:::added`), with the
  // same colours as the ve-* classes in canvas.css.
  function statusClassDefs() {
    return ['existing', 'added', 'removed', 'changed'].map(function (name) {
      return 'classDef ' + name +
        ' fill:' + cssVar('--ve-' + name + '-fill') +
        ',stroke:' + cssVar('--ve-' + name) +
        ',color:' + cssVar('--ve-fg') +
        (name === 'existing' ? '' : ',stroke-width:2px') +
        (name === 'removed' ? ',stroke-dasharray:6 4' : '');
    }).join('\n');
  }

  function mermaidSource(block) {
    // innerHTML, not textContent: a <br/> in a label must survive.
    var text = block.innerHTML
      .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
    var lines = text.replace(/^\s*\n/, '').replace(/\s+$/, '').split('\n');
    var indent = Math.min.apply(null, lines.filter(function (l) { return l.trim(); })
      .map(function (l) { return l.match(/^\s*/)[0].length; }));
    text = lines.map(function (l) { return l.slice(indent); }).join('\n');
    if (/^(flowchart|graph|stateDiagram-v2)\b/.test(text)) text += '\n' + statusClassDefs();
    return text;
  }

  function showMermaidError(block, source, message) {
    var error = document.createElement('p');
    error.className = 've-error';
    error.textContent = message;
    var pre = document.createElement('pre');
    pre.textContent = source;
    block.replaceWith(error, pre);
  }

  function loadScript(sources, done) {
    if (!sources.length) return done(false);
    var script = document.createElement('script');
    script.src = sources[0];
    script.onload = function () { done(true); };
    script.onerror = function () { script.remove(); loadScript(sources.slice(1), done); };
    document.head.appendChild(script);
  }

  function renderMermaid(blocks, done) {
    var dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    var natural = { useMaxWidth: false };
    window.mermaid.initialize({
      startOnLoad: false,
      theme: dark ? 'dark' : 'default',
      flowchart: natural, sequence: natural, state: natural, er: natural,
      class: natural, gantt: natural, journey: natural
    });
    var next = Promise.resolve();
    blocks.forEach(function (block, i) {
      var source = mermaidSource(block);
      var id = 've-mermaid-' + i;
      next = next.then(function () {
        return window.mermaid.parse(source).then(function () {
          return window.mermaid.render(id, source);
        }).then(function (result) {
          var holder = document.createElement('div');
          holder.className = 've-mermaid';
          holder.innerHTML = result.svg;
          block.replaceWith(holder);
        }).catch(function (err) {
          // A failed render can leave its work element in the document.
          var leftover = document.getElementById('d' + id);
          if (leftover) leftover.remove();
          showMermaidError(block, source, 'Mermaid: ' + (err && err.message ? err.message : err));
        });
      });
    });
    next.then(done);
  }

  // ---- start ----------------------------------------------------------------
  addArrowheads();
  sizeSvgs();
  fitAll();

  var blocks = Array.prototype.slice.call(document.querySelectorAll('pre.mermaid'));
  if (blocks.length) {
    loadScript(MERMAID_SOURCES, function (loaded) {
      if (loaded) return renderMermaid(blocks, fitAll);
      blocks.forEach(function (block) {
        showMermaidError(block, mermaidSource(block),
          'Mermaid could not be loaded (no cached copy and no network). The diagram source:');
      });
      fitAll();
    });
  }

  window.addEventListener('resize', fitAll);
  // For the per-page scripts (a toggle or a step-through that changes a frame's size).
  window.visualexplain = { fitAll: fitAll, showFrame: showFrame };
})();
