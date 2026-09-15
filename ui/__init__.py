"""Shared StayOps visual layer — theme CSS, resort assets, light 3D shells."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "images"
CSS_PATH = Path(__file__).resolve().parent / "stayops.css"

RESORT_VILLA = IMAGES / "resort1.jpeg"
RESORT_POOL = IMAGES / "resort2.jpeg"

# Served when server.enableStaticServing = true
STATIC_VILLA = "app/static/resort1.jpeg"
STATIC_POOL = "app/static/resort2.jpeg"


_TILT_JS = """
<script>
(() => {
  if (window.__stayopsTiltBound) return;
  window.__stayopsTiltBound = true;
  const attach = () => {
    document.querySelectorAll(".so-card-3d").forEach((card) => {
      if (card.dataset.tiltBound) return;
      card.dataset.tiltBound = "1";
      card.addEventListener("pointermove", (e) => {
        const r = card.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - 0.5;
        const y = (e.clientY - r.top) / r.height - 0.5;
        card.style.transform =
          "rotateY(" + (-8 + x * 14) + "deg) rotateX(" + (4 - y * 10) + "deg) translateZ(0)";
      });
      card.addEventListener("pointerleave", () => {
        card.style.transform = "";
      });
    });
  };
  attach();
  new MutationObserver(attach).observe(document.body, { childList: true, subtree: true });
})();
</script>
"""


def inject_theme() -> None:
    """Apply brand CSS (+ light 3D tilt) on every run so navigation keeps styles."""
    st.html(CSS_PATH)
    st.html(_TILT_JS, unsafe_allow_javascript=True)


def render_home_hero() -> None:
    st.html(
        f"""
<div class="so-hero" style="--so-hero-image: url('{STATIC_VILLA}');">
  <div class="so-hero__media" aria-hidden="true"></div>
  <div class="so-hero__content">
    <p class="so-brand">StayOps</p>
    <p class="so-hero__headline">Your stay, answered in seconds.</p>
    <p class="so-hero__sub",font='bold>
      Guests get property-specific help. The team asks about bookings in plain language.
    </p>
  </div>
</div>
"""
    )


def render_3d_pool_card() -> None:
    """CSS 3D-tilted resort panel using the pool image."""
    st.html(
        f"""
<div class="so-stage">
  <div class="so-card-3d">
    <img src="{STATIC_POOL}" alt="Resort pool illuminated at dusk" width="1200" height="800" />
    <div class="so-card-3d__caption">Private pool decks · evening check-in calm</div>
  </div>
</div>
"""
    )


def render_auth_banner(*, title: str, subtitle: str, image: str = STATIC_POOL) -> None:
    st.html(
        f"""
<div class="so-auth-shell" style="--so-auth-image: url('{image}');">
  <div class="so-auth-shell__bg" aria-hidden="true"></div>
  <div class="so-auth-shell__copy">
    <h2>{title}</h2>
    <p>{subtitle}</p>
  </div>
</div>
"""
    )
