FROM python:3.15-slim@sha256:044d5bd747976e21f8bc4d746c3479b19a84bb8ae6261b802acdd26b29036c93

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ cmake make \
        zlib1g-dev libjpeg-dev libfreetype6-dev liblcms2-dev libwebp-dev libtiff-dev \
    && pip install --no-cache-dir --no-compile --prefer-binary -r requirements.txt \
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

CMD ["python", "src/main.py"]