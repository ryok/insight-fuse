FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml ./

# Install dependencies only (without the local package)
RUN uv pip install --system \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    pydantic-settings==2.1.0 \
    httpx==0.25.2 \
    sqlalchemy==2.0.23 \
    alembic==1.12.1 \
    psycopg2-binary==2.9.9 \
    python-dotenv==1.0.0 \
    feedparser==6.0.10 \
    beautifulsoup4==4.12.2 \
    lxml==4.9.3 \
    openai==1.3.8 \
    anthropic==0.8.1 \
    schedule==1.2.0

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Run the application
CMD ["python", "run.py"]