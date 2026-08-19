/* Shared playbook/markdown rendering for the cloud-finops widgets.
 *
 * Inlined into widget HTML by server._load_ui() (the PLAYBOOK_RENDER
 * comment marker); edit this file, never the inlined copies.
 * Extracted from the original playbook_viewer.html so the viewer and the
 * explorer's inline playbook panel render identically.
 *
 * Deliberately NOT a general CommonMark parser: it covers what the bundled
 * playbooks and references actually use - fenced code, bullet/numbered
 * lists, bold, inline code, links, paragraphs, and (for references)
 * headings and pipe tables rendered as monospace blocks.
 */
(function () {
  "use strict";

  var SECTION_ORDER = [
    "problem", "symptoms", "detection", "fix", "anti-pattern", "see-also"
  ];
  var SECTION_LABELS = {
    "problem": "Problem",
    "symptoms": "Symptoms",
    "detection": "Detection",
    "fix": "Fix",
    "anti-pattern": "Anti-pattern",
    "see-also": "See also"
  };

  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function slugifyHeading(text) {
    return text.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
  }

  function renderInline(text) {
    var out = escapeHtml(text);
    out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
    out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    out = out.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function (_, label, href) {
      var safeHref = /^https?:\/\//.test(href) ? href : "#";
      return '<a href="' + safeHref + '" target="_blank" rel="noopener noreferrer">' + label + "</a>";
    });
    return out;
  }

  /* Render a section body. opts.checklist turns top-level list items into
   * checkbox rows (used for the Fix section; state is local to the widget
   * and never persisted). */
  function renderBody(md, opts) {
    var checklist = !!(opts && opts.checklist);
    var lines = md.split("\n");
    var html = [];
    var i = 0;
    var listBuffer = null; // {tag, items}

    function flushList() {
      if (listBuffer) {
        if (checklist) {
          html.push(
            '<ul class="checklist">' +
            listBuffer.items.map(function (it) {
              return '<li><label><input type="checkbox"><span>' +
                renderInline(it) + "</span></label></li>";
            }).join("") +
            "</ul>"
          );
        } else {
          html.push(
            "<" + listBuffer.tag + ">" +
            listBuffer.items.map(function (it) { return "<li>" + renderInline(it) + "</li>"; }).join("") +
            "</" + listBuffer.tag + ">"
          );
        }
        listBuffer = null;
      }
    }

    while (i < lines.length) {
      var line = lines[i];

      if (/^```/.test(line)) {
        flushList();
        var codeLines = [];
        i++;
        while (i < lines.length && !/^```/.test(lines[i])) {
          codeLines.push(lines[i]);
          i++;
        }
        html.push("<pre><code>" + escapeHtml(codeLines.join("\n")) + "</code></pre>");
        i++; // skip closing fence
        continue;
      }

      var bulletMatch = line.match(/^\s*[-*]\s+(.*)$/);
      var numberedMatch = line.match(/^\s*\d+\.\s+(.*)$/);

      if (bulletMatch) {
        if (!listBuffer || listBuffer.tag !== "ul") { flushList(); listBuffer = { tag: "ul", items: [] }; }
        listBuffer.items.push(bulletMatch[1]);
        i++;
        continue;
      }
      if (numberedMatch) {
        if (!listBuffer || listBuffer.tag !== "ol") { flushList(); listBuffer = { tag: "ol", items: [] }; }
        listBuffer.items.push(numberedMatch[1]);
        i++;
        continue;
      }

      // Wrapped continuation of the previous list item: indented, not a new
      // bullet/number, not blank. Source markdown wraps long bullets like
      // "- foo bar\n  baz" across two lines without repeating the marker.
      if (listBuffer && listBuffer.items.length && /^\s+\S/.test(line)) {
        listBuffer.items[listBuffer.items.length - 1] += " " + line.trim();
        i++;
        continue;
      }

      flushList();

      if (line.trim() === "") { i++; continue; }

      // Paragraph: consume until blank line / list / fence.
      var paraLines = [line];
      i++;
      while (
        i < lines.length &&
        lines[i].trim() !== "" &&
        !/^```/.test(lines[i]) &&
        !/^\s*[-*]\s+/.test(lines[i]) &&
        !/^\s*\d+\.\s+/.test(lines[i])
      ) {
        paraLines.push(lines[i]);
        i++;
      }
      html.push("<p>" + renderInline(paraLines.join(" ")) + "</p>");
    }
    flushList();
    return html.join("\n");
  }

  /* Minimal whole-document renderer for reference bodies: headings become
   * h2-h4 (h1 is the widget's own header), pipe-table blocks become
   * scrollable monospace blocks, everything else goes through renderBody. */
  function renderDocument(md) {
    var lines = md.split("\n");
    var html = [];
    var buffer = [];

    function flushBuffer() {
      if (buffer.length) {
        html.push(renderBody(buffer.join("\n")));
        buffer = [];
      }
    }

    var i = 0;
    while (i < lines.length) {
      var line = lines[i];
      var heading = line.match(/^(#{1,4})\s+(.*)$/);
      if (heading) {
        flushBuffer();
        var level = Math.max(2, Math.min(4, heading[1].length));
        html.push("<h" + level + ">" + renderInline(heading[2]) + "</h" + level + ">");
        i++;
        continue;
      }
      if (/^\s*\|/.test(line)) {
        flushBuffer();
        var tableLines = [];
        while (i < lines.length && /^\s*\|/.test(lines[i])) {
          tableLines.push(lines[i]);
          i++;
        }
        html.push('<pre class="md-table"><code>' + escapeHtml(tableLines.join("\n")) + "</code></pre>");
        continue;
      }
      if (/^---\s*$/.test(line)) { flushBuffer(); html.push("<hr>"); i++; continue; }
      buffer.push(line);
      i++;
    }
    flushBuffer();
    return html.join("\n");
  }

  function parseFrontmatter(raw) {
    var fm = {};
    var body = raw;
    if (raw.indexOf("---") === 0) {
      var end = raw.indexOf("\n---", 3);
      if (end !== -1) {
        var block = raw.slice(3, end);
        body = raw.slice(end + 4).replace(/^\n+/, "");
        block.split("\n").forEach(function (line) {
          var m = line.match(/^([a-zA-Z0-9_]+):\s*(.*)$/);
          if (m) fm[m[1]] = m[2].trim();
        });
      }
    }
    return { fm: fm, body: body };
  }

  function parseSections(body) {
    // Drop the leading "# Title" line, split the rest on "## Heading".
    var withoutTitle = body.replace(/^#\s+.*\n+/, "");
    var parts = withoutTitle.split(/\n(?=##\s+)/);
    var sections = [];
    parts.forEach(function (part) {
      var m = part.match(/^##\s+(.*)\n?([\s\S]*)$/);
      if (!m) return;
      var label = m[1].trim();
      var kind = slugifyHeading(label);
      sections.push({ kind: kind, label: label, body: m[2] });
    });
    return sections;
  }

  /* Full playbook view (header + badges + ordered sections) as an HTML
   * string. opts.checklistFix renders the Fix section as a checklist. */
  function renderPlaybookHtml(payload, opts) {
    var parsed = parseFrontmatter(payload.content);
    var fm = parsed.fm;
    var sections = parseSections(parsed.body);
    var byKind = {};
    sections.forEach(function (s) { byKind[s.kind] = s; });

    var badgeValues = [fm.scope, fm.service, fm.waste_category, fm.confidence].filter(Boolean);

    var out = [];
    out.push('<div class="header">');
    out.push("<h1>" + escapeHtml(payload.title || payload.name || "Playbook") + "</h1>");
    if (badgeValues.length) {
      out.push('<div class="badges">' + badgeValues.map(function (v) {
        return '<span class="badge">' + escapeHtml(v) + "</span>";
      }).join("") + "</div>");
    }
    out.push("</div>");

    var orderedKinds = SECTION_ORDER.slice();
    sections.forEach(function (s) { if (orderedKinds.indexOf(s.kind) === -1) orderedKinds.push(s.kind); });

    orderedKinds.forEach(function (kind) {
      var s = byKind[kind];
      if (!s) return;
      var bodyOpts = (opts && opts.checklistFix && kind === "fix") ? { checklist: true } : null;
      out.push('<div class="section" data-kind="' + kind + '">');
      out.push("<h2>" + escapeHtml(SECTION_LABELS[kind] || s.label) + "</h2>");
      out.push(renderBody(s.body, bodyOpts));
      out.push("</div>");
    });

    return out.join("\n");
  }

  /* Add a Copy button to every <pre> under root. navigator.clipboard is
   * expected to be unavailable in some host sandboxes (no clipboard-write
   * permission); the fallback selects the code so a manual Ctrl+C works,
   * and the button says so instead of lying about having copied. */
  function enhanceCodeBlocks(root) {
    var blocks = root.querySelectorAll("pre");
    Array.prototype.forEach.call(blocks, function (pre) {
      if (pre.querySelector(".copy-btn")) return;
      var btn = document.createElement("button");
      btn.className = "copy-btn";
      btn.type = "button";
      btn.textContent = "Copy";
      btn.addEventListener("click", function () {
        var text = (pre.querySelector("code") || pre).innerText;
        function flash(label) {
          btn.textContent = label;
          setTimeout(function () { btn.textContent = "Copy"; }, 1800);
        }
        function selectFallback() {
          var range = document.createRange();
          range.selectNodeContents(pre.querySelector("code") || pre);
          var sel = window.getSelection();
          sel.removeAllRanges();
          sel.addRange(range);
          var ok = false;
          try { ok = document.execCommand("copy"); } catch (e) { /* blocked */ }
          flash(ok ? "Copied" : "Selected - press Ctrl+C");
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(
            function () { flash("Copied"); },
            selectFallback
          );
        } else {
          selectFallback();
        }
      });
      pre.appendChild(btn);
    });
  }

  /* In the See also section, turn `playbooks/<slug>.md` code spans into
   * buttons that open that playbook via onOpen(slug). Reference paths stay
   * inert - they belong to the reference browser, not this widget. */
  function enhanceSeeAlso(root, onOpen) {
    var section = root.querySelector('.section[data-kind="see-also"]');
    if (!section || typeof onOpen !== "function") return;
    var codes = section.querySelectorAll("code");
    Array.prototype.forEach.call(codes, function (code) {
      var m = code.textContent.match(/^playbooks\/([a-z0-9][a-z0-9-]*)\.md$/);
      if (!m) return;
      var slug = m[1];
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "pb-link";
      btn.appendChild(code.cloneNode(true));
      btn.addEventListener("click", function () { onOpen(slug); });
      code.parentNode.replaceChild(btn, code);
    });
  }

  window.PlaybookRender = {
    SECTION_ORDER: SECTION_ORDER,
    SECTION_LABELS: SECTION_LABELS,
    escapeHtml: escapeHtml,
    renderInline: renderInline,
    renderBody: renderBody,
    renderDocument: renderDocument,
    parseFrontmatter: parseFrontmatter,
    parseSections: parseSections,
    renderPlaybookHtml: renderPlaybookHtml,
    enhanceCodeBlocks: enhanceCodeBlocks,
    enhanceSeeAlso: enhanceSeeAlso
  };
})();
