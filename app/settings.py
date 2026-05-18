from os import environ
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = PROJECT_ROOT / "site"
TEMPLATES_DIR = SITE_DIR / "templates"
STATIC_DIR = SITE_DIR / "static"
SITE_PAGES_PATH = SITE_DIR / "content/site-pages.json"

SITE_URL = environ.get("SITE_URL", "https://your-domain.com").rstrip("/")
MAX_UPLOAD_SIZE_MB = int(environ.get("MAX_UPLOAD_SIZE_MB", "50"))
