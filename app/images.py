import io
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from urllib.parse import quote

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

register_heif_opener()

INVALID_IMAGE_ERROR = "invalid_image"


class OutputFormat(str, Enum):
    jpg = "jpg"
    png = "png"


SUPPORTED_FORMATS = {
    OutputFormat.jpg: {
        "pillow_format": "JPEG",
        "media_type": "image/jpeg",
        "extension": ".jpg",
    },
    OutputFormat.png: {
        "pillow_format": "PNG",
        "media_type": "image/png",
        "extension": ".png",
    },
}


@dataclass(frozen=True)
class ConvertedImage:
    contents: io.BytesIO
    input_format: str
    media_type: str
    extension: str


def convert_image(contents: bytes, output_format: OutputFormat) -> ConvertedImage:
    config = SUPPORTED_FORMATS[output_format]

    try:
        image = Image.open(io.BytesIO(contents))
        input_format = image.format or "UNKNOWN"
        image = ImageOps.exif_transpose(image)

        if output_format == OutputFormat.jpg:
            # JPEG does not support transparency
            image = image.convert("RGB")

        output = io.BytesIO()
        image.save(output, format=config["pillow_format"])
        output.seek(0)

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid image",
            headers={"X-Error-Code": INVALID_IMAGE_ERROR},
        )

    return ConvertedImage(
        contents=output,
        input_format=input_format,
        media_type=config["media_type"],
        extension=config["extension"],
    )


def get_output_filename(filename: str | None, extension: str) -> str:
    stem = Path(filename or "converted-image").stem or "converted-image"
    return stem + extension


def get_image_formats() -> dict:
    Image.init()

    return {
        "input_formats": sorted(Image.OPEN.keys()),
        "output_formats": [format.value for format in OutputFormat],
    }


def content_disposition_inline(filename: str) -> str:
    ascii_fallback = (
        filename
        .encode("ascii", "ignore")
        .decode("ascii")
        .replace('"', "")
    ) or "download"

    utf8_filename = quote(filename, safe="")

    return (
        f'inline; filename="{ascii_fallback}"; '
        f"filename*=UTF-8''{utf8_filename}"
    )
