#!/usr/bin/env python3
"""Patch Flet Web build output with dynamic micro-stage splash screen and bridge dismiss logic."""

import os
import sys

INDEX_PATHS = [
    "build/flutter/build/web/index.html",
    "build/flutter/web/index.html",
    "build/web/index.html",
]
PYTHON_JS_PATHS = [
    "build/flutter/build/web/python.js",
    "build/flutter/web/python.js",
    "build/web/python.js",
]

SPLASH_HTML = """
<div id="asase-splash">
  <style>
    body {
      margin: 0;
      padding: 0;
      background-color: #0B0F17;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    #asase-splash {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background-color: #0B0F17;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 18px;
      z-index: 999999;
      transition: opacity 0.35s ease-out;
    }
    #asase-splash img {
      width: 80px;
      height: 80px;
      border-radius: 18px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .asase-spinner {
      width: 24px;
      height: 24px;
      border: 2.5px solid rgba(16, 185, 129, 0.2);
      border-top-color: #10B981;
      border-radius: 50%;
      animation: asase-spin 0.8s linear infinite;
    }
    .asase-status {
      font-size: 13px;
      color: #94A3B8;
      letter-spacing: 0.3px;
      font-weight: 500;
      transition: opacity 0.3s ease-in-out;
    }
    @keyframes asase-spin {
      to { transform: rotate(360deg); }
    }
    .fade-out {
      opacity: 0 !important;
      pointer-events: none;
    }
  </style>
  <img src="icon.png" alt="Asase" />
  <div class="asase-spinner"></div>
  <div id="asase-status-text" class="asase-status">Starting Earth Intelligence...</div>
  <script>
    (function() {
      var stages = [
        "Starting Earth Intelligence...",
        "Initializing telemetry core...",
        "Connecting planetary feeds..."
      ];
      var idx = 0;
      var statusEl = document.getElementById("asase-status-text");
      var timer = setInterval(function() {
        if (!document.getElementById("asase-splash")) {
          clearInterval(timer);
          return;
        }
        idx = (idx + 1) % stages.length;
        if (statusEl) {
          statusEl.style.opacity = '0';
          setTimeout(function() {
            if (statusEl) {
              statusEl.innerText = stages[idx];
              statusEl.style.opacity = '1';
            }
          }, 300);
        }
      }, 3500);
    })();
  </script>
</div>
"""

DISMISS_BRIDGE = """var splash = document.getElementById("asase-splash");
            if (splash) {
                splash.classList.add("fade-out");
                setTimeout(function() { splash.remove(); }, 350);
            }
            app.dartOnMessage(event.data);"""


def patch_web():
    patched = 0
    for INDEX_PATH in INDEX_PATHS:
        if not os.path.exists(INDEX_PATH):
            continue
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            html = f.read()
        if 'id="asase-splash"' not in html:
            # Remove native Flutter splash flash white
            html = html.replace("<body>", "<body>" + SPLASH_HTML)
            # Inject stage bus for WASM/Python progress
            if "window.__asaseStage" not in html:
                html = html.replace(
                    "</head>",
                    '<script>window.__asaseStage=function(m){var e=document.getElementById("asase-status-text");if(e){e.style.opacity="0";setTimeout(function(){e.innerText=m;e.style.opacity="1";},150);} };</script></head>',
                )
            with open(INDEX_PATH, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Patched {INDEX_PATH} with splash + stage bus")
            patched += 1
    for PYTHON_JS_PATH in PYTHON_JS_PATHS:
        if not os.path.exists(PYTHON_JS_PATH):
            continue
        with open(PYTHON_JS_PATH, "r", encoding="utf-8") as f:
            pjs = f.read()
        if "asase-splash" not in pjs and "app.dartOnMessage(event.data);" in pjs:
            pjs = pjs.replace("app.dartOnMessage(event.data);", DISMISS_BRIDGE)
            with open(PYTHON_JS_PATH, "w", encoding="utf-8") as f:
                f.write(pjs)
            print(f"Patched {PYTHON_JS_PATH} with dismissal bridge")
            patched += 1
    if patched == 0:
        print("No web build found to patch (run flet build web first)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(patch_web())
