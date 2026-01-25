from pathlib import Path
from typing import List
import logging

from PIL import Image

logger = logging.getLogger(__name__)


def check_image_valid(image_path: Path) -> bool:
    """
    Return True if the file at `image_path` is a valid image.
    """
    try:
        with Image.open(image_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def filter_invalid_images(base_path: Path) -> List[str]:
    """
    Return a list of valid image filenames found in `base_path`.
    Non-files and invalid images are filtered out.
    """
    if not base_path.exists() or not base_path.is_dir():
        return []

    potential = [p for p in base_path.iterdir() if p.is_file()]
    valid = [p.name for p in potential if check_image_valid(p)]
    return valid


def compress_image(
    src: Path, dst: Path, quality: int = 85, max_size: int = 720
) -> bool:
    """
    Compress `src` image and write it to `dst` as WEBP.
    Returns True on success, False on failure.
    """
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as img:
            rgb_im = img.convert("RGB")
            rgb_im.thumbnail((max_size, max_size))
            rgb_im.save(dst, "WEBP", quality=quality)
        return True
    except Exception as e:
        logger.warning("Error compressing image %s -> %s: %s", src, dst, e)
        return False
