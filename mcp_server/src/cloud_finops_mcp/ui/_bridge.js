/* SEP-1865 iframe<->host bridge shared by every cloud-finops widget.
 *
 * This file is inlined into each widget's HTML by server._load_ui() at
 * import time, replacing the BRIDGE comment marker. Edit THIS file; the
 * widgets never carry a hand-pasted copy. The wiring follows
 * modelcontextprotocol/ext-apps specification/2026-01-26/apps.mdx:
 *
 * - app -> host: `ui/initialize` (handshake), `tools/call` (app-initiated
 *   tool calls), `ui/open-link` (external navigation; the sandbox grants
 *   allow-scripts/allow-same-origin but not allow-popups, so target=_blank
 *   is silently swallowed).
 * - host -> app: `ui/notifications/tool-result` carrying the result of the
 *   tool call that instantiated the widget; some hosts instead answer
 *   `ui/initialize` with the payload inline.
 *
 * Failure discipline: a widget must never sit on its loading spinner with
 * no diagnostic. A host that answers ui/initialize with a JSON-RPC error,
 * never answers at all, or relays a tool result the widget cannot parse,
 * all surface as an error payload to the widget's onToolResult handler -
 * every widget already renders `{error}` payloads. A late tool-result
 * notification still re-renders over that error (self-healing).
 */
(function () {
  "use strict";

  var nextId = 100;
  var pending = {};
  var toolResultHandler = null;
  var gotResult = false;

  function post(message) {
    window.parent.postMessage(message, "*");
  }

  function deliver(payload) {
    if (toolResultHandler) {
      gotResult = true;
      toolResultHandler(payload);
    }
  }

  /* Pull the JSON payload out of a tool-result container: prefer
   * structuredContent, fall back to the first content block whose text
   * parses as JSON. Returns null when there is nothing usable. */
  function extractPayload(container) {
    if (!container) return null;
    if (container.structuredContent) return container.structuredContent;
    if (Array.isArray(container.content)) {
      for (var i = 0; i < container.content.length; i++) {
        var block = container.content[i];
        if (block && typeof block.text === "string") {
          try { return JSON.parse(block.text); } catch (e) { /* not JSON */ }
        }
      }
    }
    return null;
  }

  window.addEventListener("message", function (event) {
    var msg = event.data;
    if (!msg || msg.jsonrpc !== "2.0") return;

    if (msg.method === "ui/notifications/tool-result") {
      var payload = extractPayload(msg.params);
      if (payload) {
        deliver(payload);
      } else if (msg.params) {
        deliver({
          error: "The host relayed a tool result this widget could not " +
            "parse. The plain result is still available in the chat."
        });
      }
      return;
    }

    if (typeof msg.id === "undefined") return;

    var entry = pending[msg.id];
    if (entry) {
      delete pending[msg.id];
      if (msg.error) {
        entry.reject(new Error(msg.error.message || "The host returned an error."));
      } else {
        entry.resolve(msg.result);
      }
    }
  });

  function request(method, params, timeoutMs) {
    var ms = timeoutMs || 10000;
    return new Promise(function (resolve, reject) {
      var id = ++nextId;
      pending[id] = { resolve: resolve, reject: reject };
      post({ jsonrpc: "2.0", id: id, method: method, params: params });
      setTimeout(function () {
        if (pending[id]) {
          delete pending[id];
          reject(new Error(
            "The host did not answer " + method + " within " + ms + "ms. " +
            "It may not support app-initiated calls; ask in the chat instead."
          ));
        }
      }, ms);
    });
  }

  /* Links must not navigate the iframe: route every anchor click through
   * the host's ui/open-link. Installed once here so every widget - and the
   * playbook/reference bodies they render - inherits it; a per-widget copy
   * is how the explorer and browser shipped with dead links (the exact
   * target=_blank defect PR #135 fixed once already). The href is kept on
   * the anchor so a host without ui/open-link degrades to a no-op rather
   * than a dead element. */
  document.addEventListener("click", function (event) {
    var anchor = event.target && event.target.closest && event.target.closest("a[href]");
    if (!anchor) return;
    var href = anchor.getAttribute("href");
    if (!href || href === "#") return;
    event.preventDefault();
    request("ui/open-link", { url: href }).catch(function () { /* best effort */ });
  });

  window.McpBridge = {
    /* Announce readiness. opts.onToolResult receives the JSON payload of
     * the tool call that instantiated the widget - via the tool-result
     * notification, an inline ui/initialize result, or a synthesized
     * `{error}` payload when the handshake fails, so the widget always
     * leaves its loading state. */
    init: function (opts) {
      toolResultHandler = (opts && opts.onToolResult) || null;
      request("ui/initialize", {
        protocolVersion: "2026-01-26",
        clientInfo: { name: (opts && opts.appName) || "cloud-finops-widget", version: "1" },
        capabilities: {},
        appCapabilities: {}
      }, 15000).then(function (result) {
        // Some hosts answer the handshake with the tool result inline.
        var inline = extractPayload(result);
        if (inline) deliver(inline);
      }, function (err) {
        // Handshake error or 15s of silence. Do not clobber a result that
        // already arrived via notification; a late notification after this
        // error still re-renders over it.
        if (!gotResult) {
          deliver({
            error: "The MCP Apps handshake with the host failed (" +
              String(err && err.message || err) + "). This host may not " +
              "support interactive widgets - the tool result is still " +
              "available in the chat."
          });
          gotResult = false; // let a late notification through as first data
        }
      });
    },

    /* Call a server tool through the host. Resolves with the tool's JSON
     * payload; rejects with an actionable Error on host silence, host
     * error, or a payload that is not JSON. */
    callTool: function (name, args) {
      return request("tools/call", { name: name, arguments: args || {} })
        .then(function (result) {
          var payload = extractPayload(result);
          if (!payload) {
            throw new Error("tools/call " + name + " returned no JSON payload.");
          }
          return payload;
        });
    },

    /* Route external links through the host. Fire-and-forget: a host
     * without ui/open-link support simply does nothing. */
    openLink: function (url) {
      request("ui/open-link", { url: url }).catch(function () { /* best effort */ });
    },

    extractPayload: extractPayload
  };
})();
