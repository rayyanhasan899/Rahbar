# The evaluation suite (Parts B, C, E) as an image for the Kubernetes Job.
# Build from the repository root:  docker build -f eval/Dockerfile -t rahbar-eval:dev .
# It reuses the indexer's hashed lock (httpx, pyyaml), so no new dependency lock exists.
FROM python:3.12.16-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HOME=/tmp
WORKDIR /app
COPY indexer/requirements.lock ./requirements.lock
RUN pip install --require-hashes --only-binary=:all: --timeout 120 --retries 3 -r requirements.lock && useradd --uid 10001 --create-home app
COPY eval/*.py eval/*.yaml eval/*.jsonl eval/judge_prompt.txt ./eval/
ARG VCS_REF=development
LABEL org.opencontainers.image.revision=$VCS_REF
USER 10001:10001
CMD ["python", "eval/job.py"]
