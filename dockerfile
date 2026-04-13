FROM python:3.13-slim

RUN addgroup --system --gid 1001 appgroup
RUN adduser --system --uid 1001 --ingroup appgroup appuser

RUN pip install --no-cache-dir uv

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1
ENV UV_NO_CACHE=1

WORKDIR /app
RUN chown -R appuser:appgroup /app
COPY pyproject.toml uv.lock alembic.ini ./

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
RUN chown -R appuser:appgroup /entrypoint.sh

RUN uv venv /app/.venv
RUN uv sync --frozen --python /app/.venv/bin/python
ENV PATH="/app/.venv/bin:$PATH"

COPY --chown=appuser:appgroup ./migration ./migration
COPY --chown=appuser:appgroup ./app ./app

RUN apt-get update && apt-get install -y postgresql-client

USER appuser


CMD ["/entrypoint.sh"]