# Image Converter

## Development

Install dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the development server:

```sh
fastapi dev app/main.py
```

## Docker

Build the image:

```sh
docker build -t image-converter .
```

Run the container:

```sh
docker run --rm -p 8000:8000 -e SITE_URL=https://your-domain.com image-converter
```

## Configuration

The app is configured with environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `SITE_URL` | `https://your-domain.com` | Public site URL used for canonical URLs, social metadata, robots.txt, and sitemap.xml. |
| `MAX_UPLOAD_SIZE_MB` | `50` | Maximum uploaded image size in megabytes. |

## Asset Generation

These commands generate the static images used for browser icons and social media sharing previews.

Asset generation uses macOS Quick Look (`qlmanage`) for rendering the social media preview HTML and ImageMagick (`magick`) for image cropping and favicon output.

### Social Media Preview Image

- Source: `assets/social-media-preview.html`
- Output: `site/static/generated/social-media-preview.png`

```sh
qlmanage -t -s 1200 -o site/static/generated assets/social-media-preview.html
magick site/static/generated/social-media-preview.html.png -crop 1200x630+0+0 +repage site/static/generated/social-media-preview.png
rm site/static/generated/social-media-preview.html.png
```

### Favicons

- Source: `site/static/favicon.svg`
- Outputs:
  1. `site/static/generated/apple-touch-icon.png`
  1. `site/static/generated/favicon.ico`

```sh
magick site/static/favicon.svg -resize 180x180 site/static/generated/apple-touch-icon.png
magick site/static/favicon.svg -define icon:auto-resize=64,48,32,16 site/static/generated/favicon.ico
```
