FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir "uv==0.11.28"

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY assets ./assets
COPY dependencies ./dependencies
RUN uv sync --frozen --no-dev

RUN apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

CMD ["uv", "run", "--no-sync", "ora", "doctor", "--offline"]
