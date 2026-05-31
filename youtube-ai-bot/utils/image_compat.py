from PIL import Image

# Modern Resampling constants
if hasattr(Image, "Resampling"):
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
    RESAMPLE_BILINEAR = Image.Resampling.BILINEAR
    RESAMPLE_BICUBIC = Image.Resampling.BICUBIC
    RESAMPLE_NEAREST = Image.Resampling.NEAREST
else:
    # Deprecated fallback constants
    RESAMPLE_LANCZOS = getattr(Image, "LANCZOS", getattr(Image, "ANTIALIAS", 1))
    RESAMPLE_BILINEAR = getattr(Image, "BILINEAR", 2)
    RESAMPLE_BICUBIC = getattr(Image, "BICUBIC", 3)
    RESAMPLE_NEAREST = getattr(Image, "NEAREST", 0)

# Backward-compatible ANTIALIAS (which was deprecated in favor of LANCZOS)
if hasattr(Image, "Resampling") and hasattr(Image.Resampling, "LANCZOS"):
    RESAMPLE_ANTIALIAS = Image.Resampling.LANCZOS
else:
    RESAMPLE_ANTIALIAS = getattr(Image, "ANTIALIAS", RESAMPLE_LANCZOS)
