/* Auto-wraps glossary terms in body copy and shows a tooltip with the plain-language meaning.
   First occurrence per page, per term. Skips nav, footer, headings, code, anything inside .no-gloss. */
(function () {
  function ready(fn) { document.readyState !== 'loading' ? fn() : document.addEventListener('DOMContentLoaded', fn); }
  ready(function () {
    if (!window.GLOSSARY) return;
    var seen = new Set();
    var terms = window.GLOSSARY.terms.slice().sort(function (a, b) { return b.term.length - a.term.length; });
    var byLower = window.GLOSSARY.byTerm;
    var pattern = new RegExp('\\b(' + terms.map(function (t) { return t.term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }).join('|') + ')\\b', 'i');

    var skipSelectors = 'nav, header, .nav, .foot, footer, h1, h2, h3, h4, h5, h6, code, pre, .no-gloss, .gloss, [data-no-gloss], .canon, .canon-h, .marquee, .marquee-track, .cmd, .agent-card, .mapping-grid, .agents-grid, button, a.btn';
    var skipParents = new Set();
    document.querySelectorAll(skipSelectors).forEach(function (el) { skipParents.add(el); });

    function isSkipped(node) {
      var p = node.parentNode;
      while (p && p !== document.body) {
        if (skipParents.has(p)) return true;
        if (p.nodeType === 1) {
          var tn = p.tagName;
          if (tn === 'A' || tn === 'CODE' || tn === 'PRE' || tn === 'BUTTON') return true;
        }
        p = p.parentNode;
      }
      return false;
    }

    function walkText(root) {
      var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
      var nodes = [];
      var n;
      while ((n = walker.nextNode())) {
        if (n.nodeValue && n.nodeValue.trim() && !isSkipped(n)) nodes.push(n);
      }
      return nodes;
    }

    function wrap(textNode) {
      var text = textNode.nodeValue;
      var m = text.match(pattern);
      if (!m) return false;
      var key = m[1].toLowerCase();
      if (seen.has(key)) {
        var idx = m.index + m[0].length;
        var rest = text.slice(idx);
        if (!rest) return false;
        var restNode = document.createTextNode(rest);
        textNode.nodeValue = text.slice(0, idx);
        textNode.parentNode.insertBefore(restNode, textNode.nextSibling);
        return wrap(restNode);
      }
      var entry = byLower[key];
      if (!entry) return false;
      seen.add(key);
      var before = text.slice(0, m.index);
      var hit = m[0];
      var after = text.slice(m.index + hit.length);
      var isGlossaryPage = location.pathname.replace(/.*\//, '') === 'glossary.html';
      var dfn = document.createElement('a');
      dfn.className = 'gloss';
      dfn.dataset.slug = entry.slug;
      dfn.href = (isGlossaryPage ? '#' : 'glossary.html#') + entry.slug;
      dfn.textContent = hit;
      var parent = textNode.parentNode;
      if (before) parent.insertBefore(document.createTextNode(before), textNode);
      parent.insertBefore(dfn, textNode);
      if (after) {
        var afterNode = document.createTextNode(after);
        parent.insertBefore(afterNode, textNode);
        parent.removeChild(textNode);
        wrap(afterNode);
      } else {
        parent.removeChild(textNode);
      }
      return true;
    }

    var roots = document.querySelectorAll('main, section');
    var scope = roots.length ? roots : [document.body];
    scope.forEach(function (root) {
      walkText(root).forEach(wrap);
    });

    var tip = document.createElement('div');
    tip.className = 'gloss-tip';
    tip.setAttribute('role', 'tooltip');
    document.body.appendChild(tip);

    function show(el) {
      var entry = window.GLOSSARY.bySlug[el.dataset.slug];
      if (!entry) return;
      tip.innerHTML =
        '<div class="gt-eng">' + entry.eng + '</div>' +
        '<div class="gt-term">' + entry.term + '</div>' +
        '<p class="gt-what">' + entry.short + '</p>' +
        '<a class="gt-link" href="glossary.html#' + entry.slug + '">Full definition \u2192</a>';
      var r = el.getBoundingClientRect();
      tip.style.display = 'block';
      var w = tip.offsetWidth, h = tip.offsetHeight;
      var left = r.left + window.scrollX + r.width / 2 - w / 2;
      var top = r.bottom + window.scrollY + 10;
      left = Math.max(12, Math.min(left, window.scrollX + window.innerWidth - w - 12));
      if (top + h > window.scrollY + window.innerHeight - 12) {
        top = r.top + window.scrollY - h - 10;
      }
      tip.style.left = left + 'px';
      tip.style.top = top + 'px';
      tip.classList.add('is-open');
    }
    function hide() { tip.classList.remove('is-open'); setTimeout(function () { if (!tip.classList.contains('is-open')) tip.style.display = 'none'; }, 150); }

    var current = null;
    document.body.addEventListener('mouseover', function (e) {
      var el = e.target.closest('.gloss');
      if (el && el !== current) { current = el; show(el); }
    });
    document.body.addEventListener('mouseout', function (e) {
      var el = e.target.closest('.gloss');
      if (el && !e.relatedTarget) { hide(); current = null; }
      else if (el && !tip.contains(e.relatedTarget) && !el.contains(e.relatedTarget)) { hide(); current = null; }
    });
    document.body.addEventListener('focusin', function (e) {
      var el = e.target.closest('.gloss');
      if (el) { current = el; show(el); }
    });
    document.body.addEventListener('focusout', function (e) {
      if (e.target.closest('.gloss')) { hide(); current = null; }
    });
    var isGlossaryPage = location.pathname.replace(/.*\//, '') === 'glossary.html';
    document.body.addEventListener('click', function (e) {
      var el = e.target.closest('.gloss');
      if (el) {
        hide(); current = null;
        if (isGlossaryPage) {
          e.preventDefault();
          var target = document.getElementById(el.dataset.slug);
          if (target) { target.scrollIntoView({ behavior: 'smooth', block: 'center' }); if (window.highlight) highlight(el.dataset.slug); }
        }
        /* on other pages, let the <a> navigate naturally to glossary.html#slug */
      } else if (!tip.contains(e.target)) {
        hide(); current = null;
      }
    });
  });
})();