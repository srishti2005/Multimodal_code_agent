from __future__ import annotations

import base64
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import agent, compare, llm, render
from .models import (
    GenerateRequest,
    GenerateResponse,
    RefineRequest,
    RefineResponse,
)

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Multimodal Code Generation Agent",
    description="Text and/or screenshot -> frontend code, with an agentic self-correction loop.",
    version="0.1.0",
)

# Loosen CORS for local dev; tighten this before deploying publicly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    if not req.prompt and not req.image_base64:
        raise HTTPException(400, "Provide a text prompt, an image, or both.")
    try:
        return await agent.run_generation(
            prompt=req.prompt,
            image_base64=req.image_base64,
            image_media_type=req.image_media_type,
            framework=req.framework,
            auto_refine=req.auto_refine,
            max_iterations=req.max_iterations,
        )
    except Exception as exc:  # noqa: BLE001
        logging.exception("generation failed")
        raise HTTPException(500, f"Generation failed: {exc}") from exc


@app.post("/api/refine", response_model=RefineResponse)
async def refine(req: RefineRequest) -> RefineResponse:
    """Manual single-step refinement, e.g. triggered by an 'Iterate again' button."""
    try:
        new_code = llm.refine_code(
            code=req.code,
            feedback=req.instructions,
            image_base64=req.image_base64,
            image_media_type=req.image_media_type,
            framework=req.framework,
        )
        screenshot_b64 = None
        similarity = None
        try:
            shot = await render.screenshot_html(new_code)
            screenshot_b64 = render.bytes_to_base64(shot)
            if req.image_base64:
                ref_bytes = base64.b64decode(req.image_base64)
                similarity = compare.compare_images(ref_bytes, shot)
        except Exception as exc:  # noqa: BLE001
            logging.warning("Render during refine failed: %s", exc)

        return RefineResponse(code=new_code, screenshot_base64=screenshot_b64, similarity=similarity)
    except Exception as exc:  # noqa: BLE001
        logging.exception("refine failed")
        raise HTTPException(500, f"Refine failed: {exc}") from exc


@app.post("/api/validate")
async def validate(req: RefineRequest) -> dict:
    """Runs the code in a headless browser and returns console/page errors, if any."""
    errors = await render.validate_html(req.code)
    return {"errors": errors, "ok": len(errors) == 0}
