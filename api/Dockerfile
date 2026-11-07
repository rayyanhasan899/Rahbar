FROM python:3.12.16-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HOME=/tmp
WORKDIR /app
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements.lock ./
RUN --mount=type=cache,target=/root/.cache/pip PIP_NO_CACHE_DIR=off pip install --require-hashes --only-binary=:all: --timeout 120 --retries 3 -r requirements.lock && useradd --uid 10001 --create-home app
COPY app ./app
COPY logging.json ./logging.json
ARG VCS_REF=development
LABEL org.opencontainers.image.revision=$VCS_REF
ENV RAHBAR_REVISION=$VCS_REF
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "/app/logging.json", "--no-access-log"]
