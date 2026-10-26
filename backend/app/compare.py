"""Visual Comparator module: scores similarity between reference and generated screenshots."""
from __future__ import annotations

import io

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim


def _load_image(data: bytes, size: tuple[int, int] = (800, 600)) -> np.ndarray:
    img = Image.open(io.BytesIO(data)).convert("L")  # grayscale for SSIM
    img = img.resize(size)
    return np.array(img)


def compare_images(reference_bytes: bytes, generated_bytes: bytes) -> float:
    """Returns a similarity score in [0, 1], where 1.0 means visually identical.

    Uses SSIM (structural similarity) on grayscale, resized to a common canvas so
    differing page heights don't break the comparison. This is intentionally simple
    and fast; swap in CLIP-embedding cosine similarity or a perceptual hash if you
    want a more robust metric for the evaluation phase of the project.
    """
    ref = _load_image(reference_bytes)
    gen = _load_image(generated_bytes)
    score, _ = ssim(ref, gen, full=True)
    return float(max(0.0, min(1.0, score)))
