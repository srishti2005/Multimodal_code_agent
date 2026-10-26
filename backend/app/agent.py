"""The agentic workflow described in the project doc:

Screenshot/Text -> Generate -> Render -> Screenshot -> Compare -> Self-Correct -> repeat
"""
from __future__ import annotations

import base64
import logging
from typing import Optional

from . import compare, llm, render
from .models import GenerateResponse, IterationResult

logger = logging.getLogger("agent")

SIMILARITY_TARGET = 0.92


async def run_generation(
    prompt: str,
    image_base64: Optional[str],
    image_media_type: Optional[str],
    framework: str,
    auto_refine: bool,
    max_iterations: int,
) -> GenerateResponse:
    code = llm.generate_code(
        prompt=prompt,
        image_base64=image_base64,
        image_media_type=image_media_type,
        framework=framework,
    )

    iterations: list[IterationResult] = []
    final_similarity: Optional[float] = None
    preview_b64: Optional[str] = None

    # Render once regardless of auto_refine, so the user always gets a live preview.
    try:
        screenshot = await render.screenshot_html(code)
        preview_b64 = render.bytes_to_base64(screenshot)
    except Exception as exc:  # noqa: BLE001 - surface render failures, don't crash the request
        logger.warning("Initial render failed: %s", exc)
        screenshot = None

    if image_base64 and screenshot is not None:
        ref_bytes = base64.b64decode(image_base64)
        similarity = compare.compare_images(ref_bytes, screenshot)
        final_similarity = similarity
        iterations.append(
            IterationResult(
                iteration=0,
                code=code,
                similarity=similarity,
                screenshot_base64=preview_b64,
            )
        )

        if auto_refine:
            for i in range(1, max_iterations + 1):
                if final_similarity is not None and final_similarity >= SIMILARITY_TARGET:
                    break
                feedback = llm.describe_visual_diff(
                    reference_image_base64=image_base64,
                    generated_image_base64=preview_b64,
                    reference_media_type=image_media_type or "image/png",
                )
                code = llm.refine_code(
                    code=code,
                    feedback=feedback,
                    image_base64=image_base64,
                    image_media_type=image_media_type,
                    framework=framework,
                )
                try:
                    screenshot = await render.screenshot_html(code)
                    preview_b64 = render.bytes_to_base64(screenshot)
                    final_similarity = compare.compare_images(ref_bytes, screenshot)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Refinement render failed on iteration %s: %s", i, exc)
                    final_similarity = final_similarity  # keep previous score

                iterations.append(
                    IterationResult(
                        iteration=i,
                        code=code,
                        similarity=final_similarity,
                        feedback=feedback,
                        screenshot_base64=preview_b64,
                    )
                )

    return GenerateResponse(
        code=code,
        framework=framework,
        iterations=iterations,
        final_similarity=final_similarity,
        preview_screenshot_base64=preview_b64,
    )
