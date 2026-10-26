"""Pydantic schemas shared across the API."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Natural-language requirements for the UI.")
    image_base64: Optional[str] = Field(
        None, description="Base64-encoded reference screenshot/mockup (no data: prefix)."
    )
    image_media_type: Optional[str] = Field(
        "image/png", description="MIME type of the reference image, if provided."
    )
    framework: str = Field(
        "react-tailwind",
        description="Target stack: 'react-tailwind' or 'html-css-js'.",
    )
    auto_refine: bool = Field(
        False, description="If true and an image was provided, run the self-correction loop."
    )
    max_iterations: int = Field(3, ge=0, le=6)


class IterationResult(BaseModel):
    iteration: int
    code: str
    similarity: Optional[float] = None
    feedback: Optional[str] = None
    screenshot_base64: Optional[str] = None


class GenerateResponse(BaseModel):
    code: str
    framework: str
    iterations: List[IterationResult] = []
    final_similarity: Optional[float] = None
    preview_screenshot_base64: Optional[str] = None


class RefineRequest(BaseModel):
    code: str
    instructions: str
    image_base64: Optional[str] = None
    image_media_type: Optional[str] = "image/png"
    framework: str = "react-tailwind"


class RefineResponse(BaseModel):
    code: str
    screenshot_base64: Optional[str] = None
    similarity: Optional[float] = None
