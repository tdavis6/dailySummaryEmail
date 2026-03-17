FROM python:3.14-slim@sha256:584e89d31009a79ae4d9e3ab2fba078524a6c0921cb2711d05e8bb5f628fc9b9

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