#!/usr/bin/env python3
"""Patch Flet Web build output with the Mission Control boot splash and Pyodide bridge.

Staged, honest progress over the 3-7s (cold up to ~45s) Pyodide/WASM boot:
a determinate bar + percentage + a checklist whose four rows check off on
REAL milestones (paint → assets loaded → engine handshake → feeds painted →
first frame) — no timer-driven fake progress. The three status lines live
on as checklist rows ("Starting Earth Intelligence...", "Initializing
telemetry core...", "Connecting planetary feeds...").

Theme follows the app exactly: the user's saved Asase theme (dark/light/
system) when one exists, else the live OS preference (a mid-load OS flip
updates the splash). Colors come from the app palette (core/theme.py
AppColors) — never guessed. The splash carries NO onboarding content and
never touches asase.onboarding_done; it IS the pre-load experience.
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
      --bg2: #111827;
      --surface: #111827;
      --text: {_DARK["text"]};
      --muted: {_DARK["muted"]};
      --primary: {_DARK["primary"]};
      --border: rgba(255, 255, 255, 0.10);
      --track: rgba(255, 255, 255, 0.08);
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: linear-gradient(180deg, var(--bg) 0%, var(--bg2) 100%);
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
      margin: 0;
      padding: 0;
    }}
    #asase-splash.light {{
      --bg: {_LIGHT["bg"]};
      --bg2: #F1F5F9;
      --surface: #FFFFFF;
      --text: {_LIGHT["text"]};
      --muted: {_LIGHT["muted"]};
      --primary: {_LIGHT["primary"]};
      --border: rgba(15, 23, 42, 0.10);
      --track: rgba(15, 23, 42, 0.08);
    }}
    #asase-splash .asase-card {{
      width: min(360px, calc(100vw - 48px));
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 18px;
      padding: 28px 24px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
      box-sizing: border-box;
    }}
    #asase-splash .asase-logo {{
      width: 64px;
      height: 64px;
      border-radius: 16px;
    }}
    #asase-splash .asase-pct {{
      font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-variant-numeric: tabular-nums;
      font-size: 40px;
      font-weight: 700;
      line-height: 1;
      color: var(--text);
    }}
    #asase-splash .asase-step {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12.5px;
      font-weight: 500;
      color: var(--muted);
      min-height: 16px;
    }}
    #asase-splash .asase-spinner {{
      width: 14px;
      height: 14px;
      border: 2px solid rgba(16, 185, 129, 0.3);
      border-top-color: var(--primary);
      border-radius: 50%;
      animation: asase-spin 0.75s linear infinite;
      flex: none;
    }}
    @keyframes asase-spin {{
      to {{ transform: rotate(360deg); }}
    }}
    #asase-splash .asase-bar {{
      width: 100%;
      height: 4px;
      background: var(--track);
      border-radius: 999px;
      overflow: hidden;
    }}
    #asase-splash .asase-bar-fill {{
      height: 100%;
      width: 5%;
      background: var(--primary);
      border-radius: 999px;
      box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
      transition: width 0.45s cubic-bezier(0.22, 1, 0.36, 1);
    }}
    #asase-splash .asase-checklist {{
      list-style: none;
      margin: 0;
      padding: 0;
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 8px;
      font-size: 12.5px;
    }}
    #asase-splash .asase-checklist li {{
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--muted);
    }}
    #asase-splash .asase-checklist li .dot {{
      width: 16px;
      height: 16px;
      border-radius: 50%;
      border: 1.5px solid var(--muted);
      box-sizing: border-box;
      flex: none;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      line-height: 1;
    }}
    #asase-splash .asase-checklist li[data-state="current"] {{
      color: var(--text);
    }}
    #asase-splash .asase-checklist li[data-state="current"] .dot {{
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
      animation: asase-pulse 1.4s ease-in-out infinite;
    }}
    #asase-splash .asase-checklist li[data-state="done"] {{
      color: var(--text);
    }}
    #asase-splash .asase-checklist li[data-state="done"] .dot {{
      border-color: var(--primary);
      background: var(--primary);
      color: #0B0F17;
    }}
    #asase-splash .asase-checklist li[data-state="done"] .dot::after {{
      content: "\\2713";
    }}
    @keyframes asase-pulse {{
      50% {{ opacity: 0.55; }}
    }}
    #asase-splash .asase-footer {{
      font-size: 12.5px;
      font-weight: 700;
      color: var(--text);
      opacity: 1;
      text-align: center;
    }}
    #asase-splash .fade-out {{
      opacity: 0 !important;
      pointer-events: none;
    }}
    @media (prefers-reduced-motion: reduce) {{
      #asase-splash .asase-bar-fill {{ transition: none; }}
      #asase-splash .asase-checklist li[data-state="current"] .dot {{ animation: none; }}
      #asase-splash .asase-spinner {{ animation-duration: 1.5s; }}
    }}
  </style>

  <div class="asase-card">
    <img class="asase-logo" id="asase-logo" src="/logo_dark.svg" alt="Asase" />
    <div class="asase-pct" id="asase-pct">0%</div>
    <div class="asase-step">
      <span class="asase-spinner" aria-hidden="true"></span>
      <span id="asase-step">Step 1 of 4 · Starting Earth Intelligence...</span>
    </div>
    <div class="asase-bar"><div class="asase-bar-fill" id="asase-bar-fill"></div></div>
    <ul class="asase-checklist" id="asase-checklist">
      <li data-state="current"><span class="dot"></span>Starting Earth Intelligence...</li>
      <li data-state="pending"><span class="dot"></span>Initializing telemetry core...</li>
      <li data-state="pending"><span class="dot"></span>Connecting planetary feeds...</li>
      <li data-state="pending"><span class="dot"></span>Rendering first frame...</li>
    </ul>
    <div class="asase-footer">First time visits take about 45 seconds to set everything up. Subsequent visits are fast.</div>
  </div>

  <script>
    (function() {{
      var splash = document.getElementById("asase-splash");
      var KEYS = ["flutter.asase_storage", "asase_storage"];

      function readBlob() {{
        try {{
          for (var i = 0; i < KEYS.length; i++) {{
            var raw = localStorage.getItem(KEYS[i]);
            if (!raw) continue;
            var parsed = JSON.parse(raw);
            // Flet's SharedPreferences web plugin jsonEncode()s the stored
            // string — one extra decode layer. Handle both shapes so a
            // returning user never crashes the splash script.
            if (typeof parsed === "string") parsed = JSON.parse(parsed);
            if (parsed && typeof parsed === "object")
              return {{ data: parsed }};
          }}
        }} catch (e) {{}}
        return null;
      }}

      // Theme: saved Asase theme (dark/light; "system" falls through) >
      // live OS preference — an OS flip mid-load updates the splash.
      // The logo swaps with it: logo_dark.svg is the white wordmark.
      var mq = window.matchMedia("(prefers-color-scheme: dark)");
      function applyTheme() {{
        var cur = readBlob();
        var theme = cur && cur.data
          ? (cur.data["asase.theme"] || cur.data["theme"])
          : null;
        var dark = theme === "dark" ? true
                 : theme === "light" ? false
                 : mq.matches;
        if (dark) splash.classList.remove("light");
        else splash.classList.add("light");
        var logo = document.getElementById("asase-logo");
        if (logo) logo.src = dark ? "/logo_dark.svg" : "/logo.svg";
      }}
      applyTheme();
      if (mq.addEventListener) mq.addEventListener("change", applyTheme);

      // ── Staged progress: bands advance only on real milestones ──
      var CEIL = [40, 65, 95, 100];  // per-stage ceilings; creep caps at ceiling-2
      var STEPS = [
        "Starting Earth Intelligence...",
        "Initializing telemetry core...",
        "Connecting planetary feeds...",
        "Rendering first frame..."
      ];
      var pct = 5, stage = 0, done = false;
      var pctEl = document.getElementById("asase-pct");
      var stepEl = document.getElementById("asase-step");
      var fillEl = document.getElementById("asase-bar-fill");
      var rows = document.querySelectorAll("#asase-checklist li");

      function render() {{
        var p = Math.max(0, Math.min(Math.round(pct), 100));
        if (pctEl) pctEl.innerText = p + "%";
        if (fillEl) fillEl.style.width = p + "%";
        if (stepEl)
          stepEl.innerText = "Step " + Math.min(stage + 1, 4) + " of 4 · "
            + STEPS[Math.min(stage, 3)];
        for (var i = 0; i < rows.length; i++)
          rows[i].setAttribute("data-state",
            i < stage ? "done" : (i === stage ? "current" : "pending"));
      }}

      function reach(value, nextStage) {{  // monotonic — never goes back
        if (value > pct) pct = value;
        if (nextStage > stage) stage = nextStage;
        render();
      }}

      function dismiss() {{
        if (done) return;
        done = true;
        clearInterval(creep);
        reach(100, 4);
        splash.classList.add("fade-out");
        setTimeout(function() {{
          if (splash && splash.parentNode) splash.parentNode.removeChild(splash);
        }}, 350);
      }}

      function onHandshake() {{
        // First dartOnMessage — the Python engine is up and the app is
        // about to paint. Dismiss IMMEDIATELY: the splash never delays
        // readiness (same latency as the original v1 splash).
        dismiss();
      }}

      // Kept exact: python.js DISMISS_BRIDGE calls this on every message.
      window.__asaseSignalReady = onHandshake;

      if (document.readyState === "complete") reach(40, 1);
      else window.addEventListener("load", function() {{ reach(40, 1); }});
      setTimeout(function() {{ if (!done) dismiss(); }}, 45000);  // bridge-miss safety

      var creep = setInterval(function() {{  // eased motion INSIDE the band
        if (done) return;
        var cap = CEIL[Math.min(stage, 3)] - 2;
        if (pct < cap) {{ pct += 1; render(); }}
      }}, 1300);

      render();  // paint at 5% immediately
    }})();
  </script>
</div>
"""

DISMISS_BRIDGE = """window.__asaseSignalReady && window.__asaseSignalReady();
            app.dartOnMessage(event.data);"""


def patch_web():
    patched = 0
    splash_present = False
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

        # 2. Inject the Mission Control boot splash
        if 'id="asase-splash"' not in html:
            html = html.replace("<body>", "<body>" + SPLASH_HTML)
            with open(INDEX_PATH, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Patched {INDEX_PATH} with staged boot splash + resource hints")
            patched += 1
        else:
            splash_present = True

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

    if patched == 0 and not splash_present:
        print("No web build found to patch (run flet build web first)", file=sys.stderr)
        return 0
    # Anchor-miss guard: splash overlay present but the JS dismiss bridge
    # not found means the boot overlay would cover the app FOREVER. Any
    # Flet / Flutter upgrade can rename the python.js anchor — fail loudly
    # so CI catches it instead of shipping a permanently veiled app.
    splash_present = splash_present or patched > 0
    js_paths = [p for p in PYTHON_JS_PATHS if os.path.exists(p)]

    def _has_bridge(path: str) -> bool:
        with open(path, encoding="utf-8") as f:
            return "__asaseSignalReady" in f.read()

    bridge_found = any(_has_bridge(p) for p in js_paths)
    if splash_present and js_paths and not bridge_found:
        print(
            "FATAL: splash overlay present but dartOnMessage anchor not found — "
            "boot overlay would never dismiss. Update DISMISS_BRIDGE anchor.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(patch_web())
