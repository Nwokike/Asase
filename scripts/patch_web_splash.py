#!/usr/bin/env python3
"""Patch Flet Web build output with a simple theme-reactive boot splash and Pyodide bridge.

Pure loading state — brand icon, spinner, and rotating status lines
("Starting Earth Intelligence...", "Initializing telemetry core...",
"Connecting planetary feeds...") — covering the 3-7s Pyodide/WASM cold boot.

Theme follows the app exactly: the user's saved Asase theme (dark/light)
when one exists, else the OS preference. Colors come from the app palette
(core/theme.py AppColors) — never guessed. The splash carries NO onboarding
content and never touches asase.onboarding_done; first-run onboarding is the
in-app deck.
"""

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

# App palette (src/core/theme.py AppColors) — keep in sync with the app.
_DARK = {
    "bg": "#0B0F17",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
    "primary": "#10B981",
}
_LIGHT = {
    "bg": "#FAFAFA",
    "text": "#0F172A",
    "muted": "#64748B",
    "primary": "#059669",
}

SPLASH_HTML = f"""
<div id="asase-splash">
  <style>
    #asase-splash {{
      --bg: {_DARK["bg"]};
      --text: {_DARK["text"]};
      --muted: {_DARK["muted"]};
      --primary: {_DARK["primary"]};
    }}
    #asase-splash.light {{
      --bg: {_LIGHT["bg"]};
      --text: {_LIGHT["text"]};
      --muted: {_LIGHT["muted"]};
      --primary: {_LIGHT["primary"]};
    }}
    #asase-splash {{
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background-color: var(--bg);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      z-index: 999999;
      transition: opacity 0.35s ease-out;
      box-sizing: border-box;
      user-select: none;
      font-family: "Outfit", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: var(--text);
    }}
    #asase-splash .asase-wrap {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 22px;
      padding: 24px;
    }}
    #asase-splash .asase-logo {{
      width: 64px;
      height: 64px;
      border-radius: 16px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.25);
    }}
    #asase-splash .asase-status-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 12px;
      font-weight: 500;
      color: var(--muted);
    }}
    #asase-splash .asase-spinner {{
      width: 16px;
      height: 16px;
      border: 2px solid rgba(16, 185, 129, 0.3);
      border-top-color: var(--primary);
      border-radius: 50%;
      animation: asase-spin 0.75s linear infinite;
    }}
    @keyframes asase-spin {{
      to {{ transform: rotate(360deg); }}
    }}
    #asase-splash .fade-out {{
      opacity: 0 !important;
      pointer-events: none;
    }}
  </style>

  <div class="asase-wrap">
    <img class="asase-logo" src="icon.png" alt="Asase" />
    <div class="asase-status-row">
      <div class="asase-spinner"></div>
      <div id="asase-status-text">Starting Earth Intelligence...</div>
    </div>
  </div>

  <script>
    (function() {{
      // Theme: honor the user's saved Asase theme (SharedPreferences on web
      // prefixes localStorage keys with "flutter."; legacy walks wrote the
      // bare key), falling back to the OS preference. Never guess.
      var splash = document.getElementById("asase-splash");
      var raw = null;
      try {{
        raw = localStorage.getItem("flutter.asase_storage")
           || localStorage.getItem("asase_storage");
      }} catch (e) {{}}
      try {{
        var saved = raw ? JSON.parse(raw) : null;
        var theme = saved ? (saved["asase.theme"] || saved["theme"]) : null;
        var dark = theme === "dark" ? true
                 : theme === "light" ? false
                 : window.matchMedia("(prefers-color-scheme: dark)").matches;
        if (!dark) splash.classList.add("light");
      }} catch (e) {{
        if (!window.matchMedia("(prefers-color-scheme: dark)").matches)
          splash.classList.add("light");
      }}

      // Rotating micro-stage feedback while the WASM engine boots
      var stages = [
        "Starting Earth Intelligence...",
        "Initializing telemetry core...",
        "Connecting planetary feeds..."
      ];
      var idx = 0;
      var statusEl = document.getElementById("asase-status-text");
      var timer = setInterval(function() {{
        if (!document.getElementById("asase-splash")) {{
          clearInterval(timer);
          return;
        }}
        idx = (idx + 1) % stages.length;
        if (statusEl) {{
          statusEl.style.opacity = '0';
          setTimeout(function() {{
            if (statusEl) {{
              statusEl.innerText = stages[idx];
              statusEl.style.opacity = '1';
            }}
          }}, 300);
        }}
      }}, 3500);

      // Engine ready — fade the boot screen away. Nothing else is touched;
      // first-run onboarding is owned by the in-app deck.
      window.__asaseSignalReady = function() {{
        clearInterval(timer);
        splash.classList.add("fade-out");
        setTimeout(function() {{
          if (splash && splash.parentNode) splash.parentNode.removeChild(splash);
        }}, 350);
      }};
    }})();
  </script>
</div>
"""

DISMISS_BRIDGE = """window.__asaseSignalReady && window.__asaseSignalReady();
            app.dartOnMessage(event.data);"""


def patch_web():
    patched = 0
    for INDEX_PATH in INDEX_PATHS:
        if not os.path.exists(INDEX_PATH):
            continue
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            html = f.read()

        # 1. Inject Pyodide CDN Preconnect Resource Hints
        if 'rel="preconnect" href="https://cdn.jsdelivr.net"' not in html:
            html = html.replace(
                "<head>",
                '<head><link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin><link rel="dns-prefetch" href="https://cdn.jsdelivr.net">',
            )

        # 2. Inject Theme-Reactive Boot Splash
        if 'id="asase-splash"' not in html:
            html = html.replace("<body>", "<body>" + SPLASH_HTML)
            with open(INDEX_PATH, "w", encoding="utf-8") as f:
                f.write(html)
            print(
                f"Patched {INDEX_PATH} with theme-reactive boot splash + resource hints"
            )
            patched += 1

    for PYTHON_JS_PATH in PYTHON_JS_PATHS:
        if not os.path.exists(PYTHON_JS_PATH):
            continue
        with open(PYTHON_JS_PATH, "r", encoding="utf-8") as f:
            pjs = f.read()
        if "__asaseSignalReady" not in pjs and "app.dartOnMessage(event.data);" in pjs:
            pjs = pjs.replace("app.dartOnMessage(event.data);", DISMISS_BRIDGE)
            with open(PYTHON_JS_PATH, "w", encoding="utf-8") as f:
                f.write(pjs)
            print(f"Patched {PYTHON_JS_PATH} with readiness & dismiss signal bridge")
            patched += 1

    if patched == 0:
        print("No web build found to patch (run flet build web first)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(patch_web())
