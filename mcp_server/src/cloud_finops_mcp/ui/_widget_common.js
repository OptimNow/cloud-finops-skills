/* Shared shell helpers for the cloud-finops widgets.
 *
 * Inlined by server._load_ui() (the WIDGET_COMMON comment marker); edit
 * this file, never the inlined copies. Depends on PlaybookRender for
 * escaping, so the PLAYBOOK_RENDER marker must come first in the HTML.
 */
(function () {
  "use strict";

  var seq = 0;

  window.WidgetCommon = {
    $: function (id) { return document.getElementById(id); },
    show: function (el) { el.classList.remove("hidden"); },
    hide: function (el) { el.classList.add("hidden"); },

    /* "Filtered by the agent" chips for a find_* result's filters map.
     * Returns an HTML string (values escaped); empty string when there is
     * nothing to show. */
    chipsHtml: function (filters) {
      var keys = Object.keys(filters || {});
      if (!keys.length) return "";
      var esc = window.PlaybookRender.escapeHtml;
      return "Filtered by the agent:" + keys.map(function (k) {
        return '<span class="chip">' + esc(k) + "=" + esc(String(filters[k])) + "</span>";
      }).join("");
    },

    /* Monotonic request tokens guarding the open-detail panels: a slow
     * tools/call response that resolves after a newer interaction must
     * not overwrite the panel. Take a token before the call, bump on any
     * newer interaction (including Back), and drop the response when the
     * token is no longer current. */
    nextToken: function () { return ++seq; },
    isCurrent: function (token) { return token === seq; }
  };
})();
