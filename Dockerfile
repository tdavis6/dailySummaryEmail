FROM python:3.14-slim@sha256:f85c5697265c178cc6887276c55fe16cf3d14ca35c3df6a5eab3b360534a55d2

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --no-compile --prefer-binary -r requirements.txt \
    && find /usr/local -type d \( -name "__pycache__" -o -name "tests" -o -name "test" \) -prune -exec rm -rf '{}' + \
    && find /usr/local -type f \( -name "*.pyc" -o -name "*.pyo" -o -name "*.a" \) -delete

COPY src ./src
COPY templates ./templates
COPY static ./static
COPY version.json ./version.json

EXPOSE 8080

CMD ["python", "src/main.py"]