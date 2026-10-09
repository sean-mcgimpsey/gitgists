# Base image - install required packages.
FROM python:3.11-slim AS base

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Prevent Python from writing .pyc files and buffer outputs (ideal for Docker logging)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. Install system dependencies if required (e.g., curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy and install dependencies first (leverages Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Test stage
FROM base AS test
# Install pytest for running tests.
RUN pip install --no-cache-dir pytest
COPY . . 
RUN pytest

FROM base AS final
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
