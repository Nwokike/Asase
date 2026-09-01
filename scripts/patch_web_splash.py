#!/usr/bin/env python3
"""Patch Flet Web build output with 0ms interactive walkthrough, adaptive dark/light theme, and Pyodide bridge."""

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
    :root {
      --asase-bg: #0B0F17;
      --asase-surface: rgba(18, 26, 38, 0.88);
      --asase-border: rgba(255, 255, 255, 0.12);
      --asase-text: #F1F5F9;
      --asase-muted: #94A3B8;
      --asase-primary: #10B981;
      --asase-primary-bg: rgba(16, 185, 129, 0.15);
      --asase-primary-border: rgba(16, 185, 129, 0.35);
      --asase-card-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
    }
    @media (prefers-color-scheme: light) {
      :root {
        --asase-bg: #F8FAFC;
        --asase-surface: rgba(255, 255, 255, 0.94);
        --asase-border: rgba(0, 0, 0, 0.10);
        --asase-text: #0F172A;
        --asase-muted: #64748B;
        --asase-primary: #059669;
        --asase-primary-bg: rgba(5, 150, 105, 0.12);
        --asase-primary-border: rgba(5, 150, 105, 0.30);
        --asase-card-shadow: 0 8px 28px rgba(0, 0, 0, 0.08);
      }
    }
    body {
      margin: 0;
      padding: 0;
      background-color: var(--asase-bg);
      overflow: hidden;
      font-family: "Outfit", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: var(--asase-text);
      -webkit-font-smoothing: antialiased;
    }
    #asase-splash {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background-color: var(--asase-bg);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      z-index: 999999;
      transition: opacity 0.35s ease-out;
      box-sizing: border-box;
      user-select: none;
    }
    .asase-wrap {
      width: 100%;
      max-width: 440px;
      padding: 24px 20px;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
    }
    .asase-logo-row {
      display: flex;
      align-items: center;
      gap: 12px;
      cursor: pointer;
    }
    .asase-logo-row img {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.25);
    }
    .asase-brand-title {
      font-size: 22px;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: var(--asase-text);
      line-height: 1.1;
    }
    .asase-brand-sub {
      font-size: 9px;
      font-weight: 700;
      letter-spacing: 1.2px;
      color: var(--asase-primary);
      text-transform: uppercase;
    }
    /* Carousel Viewport */
    .asase-carousel {
      width: 100%;
      overflow: hidden;
      border-radius: 20px;
      background: var(--asase-surface);
      border: 1px solid var(--asase-border);
      box-shadow: var(--asase-card-shadow);
      backdrop-filter: blur(12px);
      position: relative;
    }
    .asase-track {
      display: flex;
      width: 400%;
      transition: transform 0.35s cubic-bezier(0.2, 0.9, 0.3, 1);
    }
    .asase-slide {
      width: 100%;
      padding: 24px 20px;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 12px;
    }
    .asase-icon-badge {
      width: 52px;
      height: 52px;
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      position: relative;
    }
    .asase-icon-badge::after {
      content: "";
      position: absolute;
      inset: -4px;
      border-radius: 20px;
      border: 1.5px solid currentColor;
      opacity: 0.25;
      animation: asase-pulse 2s infinite ease-out;
    }
    @keyframes asase-pulse {
      0% { transform: scale(0.9); opacity: 0.5; }
      100% { transform: scale(1.35); opacity: 0; }
    }
    .asase-slide h3 {
      margin: 0;
      font-size: 17px;
      font-weight: 700;
      color: var(--asase-text);
      letter-spacing: -0.2px;
    }
    .asase-slide p {
      margin: 0;
      font-size: 13px;
      line-height: 1.5;
      color: var(--asase-muted);
    }
    .asase-metric-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 600;
      background: var(--asase-primary-bg);
      border: 1px solid var(--asase-primary-border);
      color: var(--asase-text);
    }
    /* Dots navigation */
    .asase-dots {
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: center;
    }
    .asase-dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--asase-muted);
      opacity: 0.35;
      cursor: pointer;
      transition: all 0.25s ease;
    }
    .asase-dot.active {
      width: 24px;
      background: var(--asase-primary);
      opacity: 1;
    }
    /* Live Status & Spinner */
    .asase-status-row {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 12px;
      font-weight: 500;
      color: var(--asase-muted);
    }
    .asase-spinner {
      width: 16px;
      height: 16px;
      border: 2px solid var(--asase-primary-border);
      border-top-color: var(--asase-primary);
      border-radius: 50%;
      animation: asase-spin 0.75s linear infinite;
    }
    @keyframes asase-spin {
      to { transform: rotate(360deg); }
    }
    /* Actions */
    .asase-cta {
      width: 100%;
      padding: 14px 20px;
      border: none;
      border-radius: 14px;
      background: var(--asase-primary);
      color: #FFFFFF;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      box-shadow: 0 4px 18px rgba(16, 185, 129, 0.35);
      transition: all 0.2s ease;
      font-family: inherit;
    }
    .asase-cta:active {
      transform: scale(0.98);
    }
    .asase-cta.loading {
      opacity: 0.85;
      cursor: wait;
    }
    .asase-cta.ready-glow {
      box-shadow: 0 0 24px rgba(16, 185, 129, 0.65);
      animation: asase-glow 1.5s infinite alternate ease-in-out;
    }
    @keyframes asase-glow {
      from { box-shadow: 0 4px 18px rgba(16, 185, 129, 0.4); }
      to { box-shadow: 0 6px 28px rgba(16, 185, 129, 0.8); }
    }
    .asase-skip {
      background: none;
      border: none;
      color: var(--asase-muted);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      padding: 4px 8px;
      font-family: inherit;
      transition: color 0.2s;
    }
    .asase-skip:hover {
      color: var(--asase-text);
    }
    .fade-out {
      opacity: 0 !important;
      pointer-events: none;
    }
  </style>

  <div class="asase-wrap">
    <!-- Brand Header -->
    <div class="asase-logo-row">
      <img src="icon.png" alt="Asase Logo" />
      <div>
        <div class="asase-brand-title">Asase</div>
        <div class="asase-brand-sub">Earth Intelligence</div>
      </div>
    </div>

    <!-- Interactive Carousel Card -->
    <div class="asase-carousel" id="asase-carousel">
      <div class="asase-track" id="asase-track">
        <!-- Step 1: Seismic Defense -->
        <div class="asase-slide">
          <div class="asase-icon-badge" style="background: rgba(239, 68, 68, 0.15); color: #EF4444;">🌍</div>
          <h3>Planetary Seismic Defense</h3>
          <p>Real-time USGS telemetry tracking M2.5+ earthquakes globally with geodesic shockwave circles.</p>
          <div class="asase-metric-chip">⚡ 30+ Live 24h Quakes Monitored</div>
        </div>
        <!-- Step 2: NASA EONET Multi-Hazard -->
        <div class="asase-slide">
          <div class="asase-icon-badge" style="background: rgba(245, 158, 11, 0.15); color: #F59E0B;">🛰️</div>
          <h3>NASA EONET Events</h3>
          <p>Active natural event streams: wildfires, severe storms, cyclones, volcanoes, and floods.</p>
          <div class="asase-metric-chip">🔥 100 Open Natural Events</div>
        </div>
        <!-- Step 3: GloFAS & Atmospheric -->
        <div class="asase-slide">
          <div class="asase-icon-badge" style="background: rgba(14, 165, 233, 0.15); color: #0EA5E9;">🌊</div>
          <h3>Hydrology & AQI Telemetry</h3>
          <p>GloFAS 7-day river discharge forecasts, European/US air quality index, and marine telemetry.</p>
          <div class="asase-metric-chip">💧 7-Day River Discharge Forecast</div>
        </div>
        <!-- Step 4: Grounded AI Briefings -->
        <div class="asase-slide">
          <div class="asase-icon-badge" style="background: rgba(139, 92, 246, 0.15); color: #8B5CF6;">🧠</div>
          <h3>Grounded AI Briefings</h3>
          <p>Plain-language risk dossiers and vision map scans powered by Kiri Intelligence — strictly zero hallucinations.</p>
          <div class="asase-metric-chip">✨ Live Multi-Model AI Routing</div>
        </div>
      </div>
    </div>

    <!-- Navigation Dots -->
    <div class="asase-dots" id="asase-dots">
      <div class="asase-dot active" onclick="window.__asaseGo(0)"></div>
      <div class="asase-dot" onclick="window.__asaseGo(1)"></div>
      <div class="asase-dot" onclick="window.__asaseGo(2)"></div>
      <div class="asase-dot" onclick="window.__asaseGo(3)"></div>
    </div>

    <!-- Live Background Initialization Status -->
    <div class="asase-status-row">
      <div class="asase-spinner" id="asase-status-spinner"></div>
      <div id="asase-status-text">Starting Earth Intelligence...</div>
    </div>

    <!-- Primary Action Button -->
    <button id="asase-cta" class="asase-cta" onclick="window.__asaseEnter()">
      <span>Enter Planetary Command</span>
    </button>
    <button id="asase-skip" class="asase-skip" onclick="window.__asaseEnter(true)">Skip Walkthrough</button>
  </div>

  <script>
    (function() {
      var track = document.getElementById("asase-track");
      var dots = document.querySelectorAll(".asase-dot");
      var statusEl = document.getElementById("asase-status-text");
      var ctaBtn = document.getElementById("asase-cta");
      var splash = document.getElementById("asase-splash");
      var currentStep = 0;
      var totalSteps = 4;
      var isDismissed = false;
      var userPressedEnter = false;

      // Check if user is a returning visitor who already finished onboarding
      var isReturning = false;
      try {
        var raw = localStorage.getItem("asase_storage");
        if (raw) {
          var d = JSON.parse(raw);
          if (d && (d["asase.onboarding_done"] === "true" || d["asase.onboarding_done"] === true)) {
            isReturning = true;
          }
        }
      } catch(e) {}

      // Carousel Navigation
      window.__asaseGo = function(idx) {
        currentStep = Math.max(0, Math.min(totalSteps - 1, idx));
        if (track) track.style.transform = "translateX(-" + (currentStep * 25) + "%)";
        dots.forEach(function(dot, i) {
          dot.classList.toggle("active", i === currentStep);
        });
      };

      // Touch Swipe Support
      var startX = 0;
      if (track) {
        track.addEventListener("touchstart", function(e) {
          startX = e.touches[0].clientX;
        }, { passive: true });
        track.addEventListener("touchend", function(e) {
          var diff = e.changedTouches[0].clientX - startX;
          if (Math.abs(diff) > 40) {
            window.__asaseGo(currentStep + (diff < 0 ? 1 : -1));
          }
        }, { passive: true });
      }

      // Auto-advance carousel if user is idle
      var autoTimer = setInterval(function() {
        if (!isDismissed && !userPressedEnter && currentStep < totalSteps - 1) {
          window.__asaseGo(currentStep + 1);
        } else {
          clearInterval(autoTimer);
        }
      }, 3500);

      // Stage Updates from Python / WASM
      window.__asaseStage = function(msg) {
        if (statusEl) {
          statusEl.style.opacity = '0';
          setTimeout(function() {
            if (statusEl) {
              statusEl.innerText = msg;
              statusEl.style.opacity = '1';
            }
          }, 150);
        }
      };

      // Dismiss Transition
      function performDismiss() {
        if (isDismissed) return;
        isDismissed = true;
        clearInterval(autoTimer);
        if (splash) {
          splash.classList.add("fade-out");
          setTimeout(function() {
            if (splash && splash.parentNode) splash.parentNode.removeChild(splash);
          }, 350);
        }
      }

      // Record Onboarding Done in localStorage
      function markOnboardingDone() {
        try {
          var rawStorage = localStorage.getItem("asase_storage");
          var storageObj = rawStorage ? JSON.parse(rawStorage) : {};
          storageObj["asase.onboarding_done"] = "true";
          localStorage.setItem("asase_storage", JSON.stringify(storageObj));
        } catch(e) {}
      }

      // User Taps Enter or Skip
      window.__asaseEnter = function(isSkip) {
        markOnboardingDone();
        userPressedEnter = true;

        if (window.__asaseReady) {
          performDismiss();
        } else {
          // Fast onboarding completed before WASM ready -> switch button to active loader state
          if (ctaBtn) {
            ctaBtn.classList.add("loading");
            ctaBtn.innerHTML = '<div class="asase-spinner" style="border-top-color:#fff;"></div><span>Booting Planetary Command...</span>';
          }
        }
      };

      // Called when Python/Flutter engine is ready
      window.__asaseSignalReady = function() {
        window.__asaseReady = true;

        if (isReturning || userPressedEnter) {
          performDismiss();
        } else {
          // Highlight CTA with glow
          if (ctaBtn) {
            ctaBtn.classList.add("ready-glow");
            ctaBtn.innerHTML = '<span>Planetary Command Ready — Enter</span>';
          }
          if (statusEl) {
            statusEl.innerText = "Planetary Core Ready";
          }
        }
      };
    })();
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

        # 2. Inject Interactive Walkthrough & Adaptive Splash
        if 'id="asase-splash"' not in html:
            html = html.replace("<body>", "<body>" + SPLASH_HTML)
            with open(INDEX_PATH, "w", encoding="utf-8") as f:
                f.write(html)
            print(
                f"Patched {INDEX_PATH} with interactive onboarding walkthrough + resource hints"
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
