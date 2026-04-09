(function () {
  "use strict";

  function resolveBaseUrl(explicitBase) {
    if (explicitBase) {
      return String(explicitBase).replace(/\/+$/, "");
    }

    var script = document.currentScript;
    if (script && script.src) {
      try {
        var parsed = new URL(script.src);
        return (parsed.origin || "").replace(/\/+$/, "");
      } catch (error) {
        return "";
      }
    }

    return "";
  }

  function createIframe(container, options) {
    var username = options.username;
    var eventType = options.eventType;

    if (!username || !eventType) {
      throw new Error("GraftAI Embed requires both username and eventType.");
    }

    var baseUrl = resolveBaseUrl(options.baseUrl);
    var src = baseUrl + "/embed/" + encodeURIComponent(username) + "/" + encodeURIComponent(eventType);

    var iframe = document.createElement("iframe");
    iframe.src = src;
    iframe.loading = "lazy";
    iframe.allow = "clipboard-write";
    iframe.referrerPolicy = "strict-origin-when-cross-origin";
    iframe.title = options.title || "GraftAI Booking";
    iframe.style.width = "100%";
    iframe.style.height = (options.height || "760px").toString();
    iframe.style.border = "0";
    iframe.style.borderRadius = options.radius || "16px";
    iframe.style.background = "#ffffff";

    container.innerHTML = "";
    container.appendChild(iframe);
  }

  function readDataset(el) {
    return {
      username: el.getAttribute("data-username") || "",
      eventType: el.getAttribute("data-event-type") || "",
      baseUrl: el.getAttribute("data-base-url") || "",
      title: el.getAttribute("data-title") || "",
      height: el.getAttribute("data-height") || "760px",
      radius: el.getAttribute("data-radius") || "16px",
    };
  }

  function mount(container, config) {
    var merged = Object.assign({}, readDataset(container), config || {});
    createIframe(container, merged);
  }

  function autoMount() {
    var targets = document.querySelectorAll("[data-graftai-embed]");
    for (var i = 0; i < targets.length; i += 1) {
      try {
        mount(targets[i]);
      } catch (error) {
        // Swallow to avoid breaking host pages.
      }
    }
  }

  window.GraftAIEmbed = {
    mount: mount,
    autoMount: autoMount,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", autoMount);
  } else {
    autoMount();
  }
})();
