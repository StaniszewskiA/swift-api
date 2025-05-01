FROM python:3.11-alpine AS builder

RUN apk add --no-cache curl gcc libffi-dev musl-dev

RUN pip install poetry==1.6.1

ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /build

COPY pyproject.toml poetry.lock ruff.toml ./

RUN poetry install --no-root --no-dev

FROM python:3.11-alpine

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY . /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]