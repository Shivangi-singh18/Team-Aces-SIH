"""Image ingestion and preprocessing utilities for Medical Document OCR.

Handles ingestion of paths, raw bytes, BytesIO, base64 strings, and PIL Images.
Applies preprocessing optimizations (EXIF orientation, grayscale, contrast enhancement,
and resizing) for challenging OPD prescription captures.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Tuple, Union

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ImageInput = Union[str, Path, bytes, io.BytesIO, Image.Image]


class ImagePreprocessor:
    """Ingests and preprocesses medical document images for OCR extraction."""

    @staticmethod
    def load_image(image_input: ImageInput) -> Image.Image:
        """Load an image from various input types and correct its orientation.

        Args:
            image_input: File path, base64 string, raw bytes, BytesIO, or PIL Image.

        Returns:
            PIL.Image.Image: Normalized RGB image with correct EXIF orientation.

        Raises:
            ValueError: If input format is unsupported or data cannot be decoded.
        """
        img: Image.Image

        if isinstance(image_input, Image.Image):
            img = image_input
        elif isinstance(image_input, (str, Path)):
            path_str = str(image_input).strip()
            # Check if it is a base64 string rather than a file path
            if path_str.startswith("data:image/") or (len(path_str) > 260 and "\n" not in path_str and not Path(path_str).exists()):
                img = ImagePreprocessor._load_from_base64(path_str)
            else:
                p = Path(path_str)
                if not p.exists():
                    raise FileNotFoundError(f"Medical document image not found at: {p}")
                img = Image.open(p)
        elif isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, io.BytesIO):
            image_input.seek(0)
            img = Image.open(image_input)
        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")

        # Automatically transpose based on EXIF tag (critical for phone camera shots)
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Convert palette/RGBA to standard RGB
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        return img

    @staticmethod
    def _load_from_base64(b64_str: str) -> Image.Image:
        """Decode base64 string with optional data URI prefix."""
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]
        decoded_bytes = base64.b64decode(b64_str)
        return Image.open(io.BytesIO(decoded_bytes))

    @staticmethod
    def to_bytes(image: Image.Image, format: str = "JPEG", quality: int = 92) -> bytes:
        """Convert a PIL Image to raw bytes."""
        buffer = io.BytesIO()
        # Save as PNG if RGBA, or JPEG otherwise
        fmt = "PNG" if image.mode == "RGBA" else format
        if fmt == "JPEG" and image.mode == "RGBA":
            image = image.convert("RGB")
        image.save(buffer, format=fmt, quality=quality)
        return buffer.getvalue()

    @staticmethod
    def preprocess_for_ocr(
        image_input: ImageInput,
        grayscale: bool = True,
        enhance_contrast: bool = True,
        contrast_factor: float = 1.6,
        sharpen: bool = True,
        max_dimension: int = 2400,
    ) -> Image.Image:
        """Preprocess medical document image to optimize OCR accuracy.

        Performs:
        1. Downscaling if larger than max_dimension to preserve memory/speed.
        2. EXIF auto-rotation.
        3. Grayscale conversion.
        4. Auto-contrast or linear contrast expansion.
        5. Light sharpening to clarify doctor handwriting strokes.

        Args:
            image_input: Input document representation.
            grayscale: Convert to 8-bit grayscale.
            enhance_contrast: Boost contrast to distinguish ink from paper.
            contrast_factor: Multiplier for contrast enhancement.
            sharpen: Apply slight sharpening filter.
            max_dimension: Maximum width/height in pixels.

        Returns:
            Preprocessed PIL.Image.Image.
        """
        img = ImagePreprocessor.load_image(image_input)

        # Scale down if extremely large
        w, h = img.size
        if max(w, h) > max_dimension:
            scale = max_dimension / float(max(w, h))
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        if grayscale and img.mode != "L":
            img = img.convert("L")

        if enhance_contrast:
            # Auto-contrast expands min and max intensities
            img = ImageOps.autocontrast(img, cutoff=1)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast_factor)

        if sharpen:
            img = img.filter(ImageFilter.SHARPEN)

        return img

    @staticmethod
    def binarize(image: Image.Image, threshold: int = 140) -> Image.Image:
        """Convert image to clean black and white binary bitmap."""
        if image.mode != "L":
            image = image.convert("L")
        return image.point(lambda p: 255 if p > threshold else 0, mode="1")
