FROM python:3.13-slim as builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY uv.lock pyproject.toml ./

RUN uv sync --frozen --no-install-project --no-dev

FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "drm_document_service.app:app", "--host", "0.0.0.0", "--port", "8000"]
