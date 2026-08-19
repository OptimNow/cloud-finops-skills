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
 */
(function () {
  "use strict";

  var INIT_ID = 1;
  var nextId = 100;
  var pending = {};
  var toolResultHandler = null;

  function post(message) {
    window.parent.postMessage(message, "*");
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
      if (toolResultHandler) {
        var payload = extractPayload(msg.params);
        if (payload) toolResultHandler(payload);
      }
      return;
    }

    if (typeof msg.id === "undefined") return;

    /* Some hosts answer ui/initialize with the initial tool result inline
     * rather than as a separate notification. */
    if (msg.id === INIT_ID && msg.result) {
      var inline = extractPayload(msg.result);
      if (inline && toolResultHandler) toolResultHandler(inline);
      return;
    }

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

  window.McpBridge = {
    /* Announce readiness. opts.onToolResult receives the JSON payload of
     * the tool call that instantiated the widget (via notification or
     * inline initialize result). */
    init: function (opts) {
      toolResultHandler = (opts && opts.onToolResult) || null;
      post({
        jsonrpc: "2.0",
        id: INIT_ID,
        method: "ui/initialize",
        params: {
          protocolVersion: "2026-01-26",
          clientInfo: { name: (opts && opts.appName) || "cloud-finops-widget", version: "1" },
          capabilities: {},
          appCapabilities: {}
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
