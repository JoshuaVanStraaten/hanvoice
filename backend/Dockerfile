# HanVoice API — multi-stage build, non-root runtime.
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim

# Never run as root; the app needs no OS packages beyond the base image.
RUN groupadd --system hanvoice && useradd --system --gid hanvoice hanvoice

WORKDIR /srv
COPY --from=builder /install /usr/local
COPY app ./app

USER hanvoice
EXPOSE 8000

# Single worker per container; scale with replicas, not processes — the
# in-process rate limiter assumes one process per instance.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
