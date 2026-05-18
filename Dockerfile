# syntax=docker/dockerfile:1.7

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_DIR=/data

WORKDIR /app

RUN --mount=type=bind,source=requirements.txt,target=/tmp/requirements.txt,readonly \
    pip install --disable-pip-version-check --no-cache-dir -r /tmp/requirements.txt

RUN mkdir /data && \
    chown nobody:nogroup /data

COPY app ./app
COPY site ./site

USER nobody

EXPOSE 8000

CMD ["fastapi", "run"]
