FROM python:3.12-slim

WORKDIR /app

# Install uv package manager
RUN pip install uv

# Install dependencies
COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

# Copy application code
COPY . .
RUN mkdir -p data output

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
