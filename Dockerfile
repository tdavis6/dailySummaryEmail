FROM python:3.14-slim@sha256:b877e50bd90de10af8d82c57a022fc2e0dc731c5320d762a27986facfc3355c1

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