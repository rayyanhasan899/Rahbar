FROM python:3.12.16-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HOME=/tmp
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng poppler-utils && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt requirements.lock ./
RUN --mount=type=cache,target=/root/.cache/pip PIP_NO_CACHE_DIR=off pip install --require-hashes --only-binary=:all: --timeout 120 --retries 3 -r requirements.lock && useradd --uid 10001 --create-home app
COPY pipeline ./pipeline
ARG VCS_REF=development
LABEL org.opencontainers.image.revision=$VCS_REF
USER 10001:10001
CMD ["python", "-m", "pipeline.run"]
