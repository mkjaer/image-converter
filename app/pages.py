import json

from app.settings import SITE_PAGES_PATH

with SITE_PAGES_PATH.open() as page_data_file:
    PAGE_DATA = json.load(page_data_file)

HOME_PAGE = PAGE_DATA["home"]
CONVERSION_PAGES = PAGE_DATA["conversion_pages"]
