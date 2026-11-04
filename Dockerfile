FROM python:3.15-slim@sha256:8c13a3f37a6a5b71498228e902c4b9f51c1f7900d49fabf71f9a650c6120e0d0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt requirements-nodeps.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ cmake make \
        zlib1g-dev libjpeg-dev libfreetype6-dev liblcms2-dev libwebp-dev libtiff-dev \
    && pip install --no-cache-dir --no-compile --prefer-binary -r requirements.txt \
    && pip install --no-cache-dir --no-compile --prefer-binary --no-deps -r requirements-nodeps.txt \
    && python -c "import caldav, recurring_ical_events" \
    && apt-get purge -y --auto-remove \
        gcc g++ cmake make \
        zlib1g-dev libjpeg-dev libfreetype6-dev liblcms2-dev libwebp-dev libtiff-dev \
    && apt-get install -y --no-install-recommends \
        libjpeg62-turbo libfreetype6 liblcms2-2 libwebp7 libwebpmux3 libwebpdemux2 libtiff6 \
    && rm -rf /var/lib/apt/lists/* \
    && find /usr/local -type d \( -name "__pycache__" -o -name "tests" -o -name "test" \) -prune -exec rm -rf '{}' + \
    && find /usr/local -type f \( -name "*.pyc" -o -name "*.pyo" -o -name "*.a" \) -delete

COPY src ./src
COPY templates ./templates
COPY static ./static
COPY version.json ./version.json

EXPOSE 8080

HEALTHCHECK --interval=60s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/login', timeout=4)" || exit 1

CMD ["python", "src/main.py"]