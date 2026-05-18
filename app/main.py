from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.images import OutputFormat, convert_image, get_image_formats, get_output_filename
from app.pages import CONVERSION_PAGES, HOME_PAGE
from app.settings import MAX_UPLOAD_SIZE_MB, SITE_URL, STATIC_DIR, TEMPLATES_DIR
from app.uploads import read_upload_file

app = FastAPI()

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


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


@app.get("/formats/")
async def get_supported_formats():
    return get_image_formats()


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
    contents = await read_upload_file(
        file=file,
        max_size_mb=MAX_UPLOAD_SIZE_MB,
    )

    try:
        converted_image = convert_image(contents, format)
    finally:
        await file.close()

    filename = get_output_filename(file.filename, converted_image.extension)

    return StreamingResponse(
        converted_image.contents,
        media_type=converted_image.media_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"'
        },
    )
