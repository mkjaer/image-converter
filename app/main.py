from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.images import (
    OutputFormat,
    content_disposition_inline,
    convert_image,
    get_image_formats,
    get_output_filename,
)
from app.pages import CONVERSION_PAGES, HOME_PAGE
from app.settings import DATABASE_PATH, MAX_UPLOAD_SIZE_MB, SITE_URL, STATIC_DIR, TEMPLATES_DIR
from app.stats import (
    get_conversion_stats,
    increment_conversion_count,
    increment_failure_count,
    increment_failure_detail_count,
    initialize_stats_database,
)
from app.uploads import read_upload_file

app = FastAPI()
initialize_stats_database(DATABASE_PATH)

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

CONVERSION_ERROR = "conversion_error"
FILE_TOO_LARGE_ERROR = "file_too_large"
INVALID_IMAGE_ERROR = "invalid_image"


def get_upload_extension(file: UploadFile) -> str:
    return Path(file.filename or "").suffix.lower() or "none"


def get_upload_content_type(file: UploadFile) -> str:
    return file.content_type or "unknown"


def render_index(request: Request, page: dict, path: str = "/"):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "page": page,
            "page_url": f"{SITE_URL}{path}",
            "site_url": SITE_URL,
        },
    )


@app.get("/")
async def index(request: Request):
    return render_index(request, HOME_PAGE)


@app.get("/health/")
async def health():
    return {"status": "ok"}


@app.get("/formats/")
async def get_supported_formats():
    return get_image_formats()


@app.get("/stats/")
async def stats():
    return get_conversion_stats(DATABASE_PATH)


@app.get("/robots.txt")
async def robots_txt():
    template = templates.get_template("robots.txt")
    return Response(
        content=template.render(site_url=SITE_URL),
        media_type="text/plain",
    )


@app.get("/sitemap.xml")
async def sitemap_xml():
    template = templates.get_template("sitemap.xml")
    return Response(
        content=template.render(
            pages=["/"] + [f"/{slug}/" for slug in CONVERSION_PAGES],
            site_url=SITE_URL,
        ),
        media_type="application/xml",
    )


@app.get("/{slug}/")
async def conversion_page(request: Request, slug: str):
    page = CONVERSION_PAGES.get(slug)

    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")

    return render_index(request, page, path=f"/{slug}/")


@app.post("/convert/")
async def convert_file(
    file: UploadFile,
    format: OutputFormat = OutputFormat.jpg,
):
    try:
        contents = await read_upload_file(
            file=file,
            max_size_mb=MAX_UPLOAD_SIZE_MB,
        )
        converted_image = convert_image(contents, format)
        increment_conversion_count(
            database_path=DATABASE_PATH,
            input_format=converted_image.input_format,
            output_format=format.value,
        )
    except HTTPException as error:
        reason = (error.headers or {}).get("X-Error-Code", CONVERSION_ERROR)
        increment_failure_count(DATABASE_PATH, reason)

        if reason == INVALID_IMAGE_ERROR:
            increment_failure_detail_count(
                DATABASE_PATH,
                reason=reason,
                detail_type="extension",
                detail_value=get_upload_extension(file),
            )
            increment_failure_detail_count(
                DATABASE_PATH,
                reason=reason,
                detail_type="content_type",
                detail_value=get_upload_content_type(file),
            )

        if reason == FILE_TOO_LARGE_ERROR:
            increment_failure_detail_count(
                DATABASE_PATH,
                reason=reason,
                detail_type="limit_mb",
                detail_value=str(MAX_UPLOAD_SIZE_MB),
            )

        raise
    except Exception:
        increment_failure_count(DATABASE_PATH, CONVERSION_ERROR)
        raise
    finally:
        await file.close()

    filename = get_output_filename(file.filename, converted_image.extension)

    return StreamingResponse(
        converted_image.contents,
        media_type=converted_image.media_type,
        headers={
            "Content-Disposition": content_disposition_inline(filename)
        },
    )
