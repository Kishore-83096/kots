from io import BytesIO

try:
    from PIL import Image, ImageOps, UnidentifiedImageError
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    Image = None
    ImageOps = None
    UnidentifiedImageError = Exception


TARGET_IMAGE_SIZE_KB = 100
TARGET_IMAGE_SIZE_BYTES = TARGET_IMAGE_SIZE_KB * 1024
INITIAL_JPEG_QUALITY = 85
MIN_JPEG_QUALITY = 35
QUALITY_STEP = 5
RESIZE_RATIO = 0.9
MIN_SIDE_PX = 480


def _to_rgb(image):
    if image.mode == "RGB":
        return image
    if image.mode in ("RGBA", "LA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        return background
    return image.convert("RGB")


def _save_as_jpeg(image, quality):
    output = BytesIO()
    image.save(output, format="JPEG", quality=quality, optimize=True)
    output.seek(0)
    return output


def compress_image_to_100kb(file):
    if not file:
        return None, "Image file is required."

    if Image is None or ImageOps is None:
        # Pillow unavailable: keep uploads working instead of breaking app startup.
        return file, None

    try:
        file.stream.seek(0)
        with Image.open(file.stream) as source:
            working = _to_rgb(ImageOps.exif_transpose(source))
    except (UnidentifiedImageError, OSError, ValueError):
        return None, "Uploaded file is not a valid image."
    finally:
        try:
            file.stream.seek(0)
        except Exception:
            pass

    best_output = None
    current = working

    while True:
        for quality in range(INITIAL_JPEG_QUALITY, MIN_JPEG_QUALITY - 1, -QUALITY_STEP):
            candidate = _save_as_jpeg(current, quality)
            if candidate.getbuffer().nbytes <= TARGET_IMAGE_SIZE_BYTES:
                candidate.name = file.filename or "upload.jpg"
                return candidate, None
            best_output = candidate

        next_width = int(current.width * RESIZE_RATIO)
        next_height = int(current.height * RESIZE_RATIO)
        if next_width < MIN_SIDE_PX or next_height < MIN_SIDE_PX:
            break
        current = current.resize((next_width, next_height), Image.LANCZOS)

    if best_output:
        best_output.name = file.filename or "upload.jpg"
        return best_output, None

    return None, "Unable to process image."
