"""Thin wrapper around the Anthropic API for multimodal (image + text) code generation.

Swap this module out if you want to use a different vision-capable LLM
(GPT-4o, Gemini, open-weight models via Ollama, etc.) — everything else in
the app only depends on `generate_code()` and `refine_code()` below.
"""
from __future__ import annotations

import os
import re
from typing import Optional

import anthropic

MODEL = os.environ.get("AGENT_MODEL", "claude-sonnet-4-5")

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

SYSTEM_PROMPT = """You are an expert frontend engineer working inside an autonomous \
code-generation agent. You produce a SINGLE self-contained HTML document that:

- Uses Tailwind CSS via the CDN script tag (https://cdn.tailwindcss.com).
- If the target framework is 'react-tailwind', also loads React, ReactDOM and \
Babel standalone via CDN and writes the app inside a <script type="text/babel"> \
tag that mounts to a #root div. If the target framework is 'html-css-js', write \
plain semantic HTML/CSS/vanilla JS instead (no React).
- Is fully self-contained (no external build step, no bare npm imports) so it can \
be rendered directly by setting it as an iframe's srcdoc.
- Closely matches any reference screenshot provided: layout, spacing, colors, \
typography, icons (use inline SVG or a CDN icon font), and visible text.
- Is responsive and uses semantic, accessible markup.

Rules for your reply:
1. Reply with ONLY one ```html fenced code block containing the complete document \
(<!DOCTYPE html> ... </html>). No prose before or after the code block.
2. Do not truncate the document. Do not use placeholder comments like \
"<!-- rest of the code -->" — always emit real, complete code.
"""


def _extract_code_block(text: str) -> str:
    match = re.search(r"```(?:html)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def _build_user_content(
    prompt: str,
    image_base64: Optional[str],
    image_media_type: Optional[str],
    framework: str,
) -> list:
    content: list = []
    if image_base64:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_media_type or "image/png",
                    "data": image_base64,
                },
            }
        )
    instruction = (
        f"Target framework: {framework}\n\n"
        f"User requirements: {prompt or '(none — infer everything from the screenshot)'}\n\n"
        "Generate the complete self-contained HTML document now."
    )
    content.append({"type": "text", "text": instruction})
    return content


def generate_code(
    prompt: str,
    image_base64: Optional[str] = None,
    image_media_type: Optional[str] = "image/png",
    framework: str = "react-tailwind",
) -> str:
    """Image+Text -> Code (or Text -> Code when no image is given)."""
    message = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": _build_user_content(prompt, image_base64, image_media_type, framework),
            }
        ],
    )
    text = "".join(block.text for block in message.content if block.type == "text")
    return _extract_code_block(text)


def refine_code(
    code: str,
    feedback: str,
    image_base64: Optional[str] = None,
    image_media_type: Optional[str] = "image/png",
    framework: str = "react-tailwind",
) -> str:
    """Self-correction step: feed the current code + a diff/critique back to the model."""
    content: list = []
    if image_base64:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_media_type or "image/png",
                    "data": image_base64,
                },
            }
        )
        content.append({"type": "text", "text": "Reference screenshot (target design) above."})

    content.append(
        {
            "type": "text",
            "text": (
                f"Here is the CURRENT generated code (framework: {framework}):\n\n"
                f"```html\n{code}\n```\n\n"
                f"Feedback / detected differences from the reference:\n{feedback}\n\n"
                "Revise the code to fix these issues. Reply with the complete corrected "
                "self-contained HTML document, same rules as before."
            ),
        }
    )

    message = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    text = "".join(block.text for block in message.content if block.type == "text")
    return _extract_code_block(text)


def describe_visual_diff(
    reference_image_base64: str,
    generated_image_base64: str,
    reference_media_type: str = "image/png",
) -> str:
    """Ask the vision model to describe concrete differences between two screenshots.

    This text becomes the `feedback` passed into refine_code() for the next iteration.
    """
    message = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=(
            "You compare two UI screenshots: a REFERENCE design and a GENERATED "
            "implementation. List concrete, actionable differences (spacing, colors, "
            "font sizes, alignment, missing/extra components, wrong text, layout "
            "breakpoints). Be specific and terse — bullet points only, no preamble."
        ),
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": reference_media_type,
                            "data": reference_image_base64,
                        },
                    },
                    {"type": "text", "text": "^ REFERENCE design"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": generated_image_base64,
                        },
                    },
                    {"type": "text", "text": "^ GENERATED implementation. List the differences."},
                ],
            }
        ],
    )
    return "".join(block.text for block in message.content if block.type == "text")
