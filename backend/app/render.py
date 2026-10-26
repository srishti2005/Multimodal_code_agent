"""Renders generated HTML in a headless browser and captures a screenshot.

This is the 'UI Renderer' module from the architecture doc: it lets the agent
see its own output so the Visual Comparator / Self-Correction loop can work.
"""
from __future__ import annotations

import base64

from playwright.async_api import async_playwright

DEFAULT_VIEWPORT = {"width": 1280, "height": 800}


async def screenshot_html(html: str, viewport: dict | None = None, timeout_ms: int = 15000) -> bytes:
    """Render a self-contained HTML string and return a PNG screenshot as bytes.

    Uses `page.set_content` with `srcdoc`-equivalent semantics (data isn't written
    to disk), and waits for network/CDN scripts (Tailwind, React, Babel) to settle.
    """
    viewport = viewport or DEFAULT_VIEWPORT
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        try:
            page = await browser.new_page(viewport=viewport)
            await page.set_content(html, wait_until="networkidle", timeout=timeout_ms)
            # Give CDN-loaded React/Babel a brief moment to hydrate after networkidle.
            await page.wait_for_timeout(300)
            png_bytes = await page.screenshot(full_page=True)
            return png_bytes
        finally:
            await browser.close()


async def validate_html(html: str, timeout_ms: int = 15000) -> list[str]:
    """Load the page and collect console errors / page errors. Empty list = clean load."""
    errors: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        try:
            page = await browser.new_page()
            page.on("console", lambda msg: errors.append(f"console.{msg.type}: {msg.text}") if msg.type == "error" else None)
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            await page.set_content(html, wait_until="networkidle", timeout=timeout_ms)
            await page.wait_for_timeout(300)
        finally:
            await browser.close()
    return errors


def bytes_to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")
