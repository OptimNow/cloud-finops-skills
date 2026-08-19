/* Shared playbook/markdown rendering for the cloud-finops widgets.
 *
 * Inlined into widget HTML by server._load_ui() (the PLAYBOOK_RENDER
 * comment marker); edit this file, never the inlined copies. Extracted
 * from the original playbook_viewer.html so the viewer and the explorer's
 * inline playbook panel render identically.
 *
 * Deliberately NOT a general CommonMark parser: it covers what the bundled
 * playbooks and references actually use - fenced code, bullet/numbered
 * lists, bold, inline code, links, paragraphs, and (for references)
 * headings and pipe tables rendered as monospace blocks.
 *
 * Two hard-won rules encoded here:
 * - Fence state is tracked EVERYWHERE lines are scanned. The reference
 *   bodies carry KQL ('| where ...') and bash comments ('# ...') inside
 *   fences; a fence-blind scanner turns them into tables and headings and
 *   corrupts everything after (found on finops-azure, 83 such lines).
 * - HTML comments are stripped outside fences. The content carries
 *   maintainer/provenance comments that proper markdown renderers hide;
 *   escapeHtml would print them as visible text.
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

  /* Escape for BOTH element text and double/single-quoted attribute
   * values. Quotes matter: renderInline interpolates link targets into
   * href="..." and the explorer puts facet values into data-/title=
   * attributes - without quote escaping, a crafted value breaks out of
   * the attribute. */
  function escapeHtml(s) {
    return s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function slugifyHeading(text) {
    return text.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
  }

  function renderInline(text) {
    // Protect inline code spans first: their content must render literally,
    // not be re-processed by the bold/link passes below (a `[x](y)` inside
    // backticks is code, not a link).
    var codes = [];
    var masked = text.replace(/`([^`]+)`/g, function (_, code) {
      codes.push(code);
      // U+0000 sentinels: cannot occur in markdown text, so the restore
      // pass below can never collide with real content.
      return "\u0000" + (codes.length - 1) + "\u0000";
    });
    var out = escapeHtml(masked);
    // Drop inline HTML comments (provenance markers etc.) - a markdown
    // renderer hides them; printing them as text is the bug.
    out = out.replace(/&lt;!--[\s\S]*?--&gt;/g, "");
    out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    out = out.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function (_, label, href) {
      var safeHref = /^https?:\/\//.test(href) ? href : "#";
      return '<a href="' + safeHref + '" target="_blank" rel="noopener noreferrer">' + label + "</a>";
    });
    out = out.replace(/\u0000(\d+)\u0000/g, function (_, n) {
      return "<code>" + escapeHtml(codes[Number(n)]) + "</code>";
    });
    return out;
  }

  /* Render a section body. opts.checklist turns NUMBERED (ol) top-level
   * items into checkbox rows that keep their step numbers via CSS
   * counters; bullet sub-lists stay plain bullets, so an explanatory
   * sub-item can never be "checked off" as if it were an action. State is
   * local to the widget and never persisted. */
  function renderBody(md, opts) {
    var checklist = !!(opts && opts.checklist);
    var lines = md.split("\n");
    var html = [];
    var i = 0;
    var listBuffer = null; // {tag, items}

    function flushList() {
      if (!listBuffer) return;
      if (checklist && listBuffer.tag === "ol") {
        html.push(
          '<ol class="checklist">' +
          listBuffer.items.map(function (it) {
            return '<li><label><input type="checkbox"><span>' +
              renderInline(it) + "</span></label></li>";
          }).join("") +
          "</ol>"
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

      // Whole-line/blocked HTML comments (provenance markers, maintainer
      // notes): consume through the closing marker and emit nothing.
      if (/^\s*<!--/.test(line)) {
        flushList();
        while (i < lines.length && lines[i].indexOf("-->") === -1) i++;
        i++; // skip the line carrying -->
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
   * scrollable monospace blocks, everything else goes through renderBody.
   * Heading/table/hr detection is fence-aware: inside a fence, every line
   * belongs to the buffered code and is handed to renderBody untouched. */
  function renderDocument(md) {
    var lines = md.split("\n");
    var html = [];
    var buffer = [];
    var inFence = false;

    function flushBuffer() {
      if (buffer.length) {
        html.push(renderBody(buffer.join("\n")));
        buffer = [];
      }
    }

    var i = 0;
    while (i < lines.length) {
      var line = lines[i];
      if (/^```/.test(line)) {
        inFence = !inFence;
        buffer.push(line);
        i++;
        continue;
      }
      if (inFence) {
        buffer.push(line);
        i++;
        continue;
      }
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

  /* Human-readable text for a tool error payload, suggestions included.
   * Callers must put this in textContent (or escape it) - it is plain
   * text, and suggestions come from tool data. */
  function errorText(payload) {
    var text = String(payload.error || "The tool returned an error.");
    if (payload.suggestions && payload.suggestions.length) {
      text += "\nDid you mean: " + payload.suggestions.join(", ") + "?";
    }
    return text;
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
    errorText: errorText,
    enhanceCodeBlocks: enhanceCodeBlocks,
    enhanceSeeAlso: enhanceSeeAlso
  };
})();
