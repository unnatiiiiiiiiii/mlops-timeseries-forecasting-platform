FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required by ML libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.api.txt .
RUN pip install --no-cache-dir -r requirements.api.txt

# Copy application code
COPY src/ /app/src/
COPY services/ /app/services/

# Create required directories
RUN mkdir -p /app/models /app/data

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port for FastAPI
EXPOSE 8000

# Start FastAPI inference API
CMD ["uvicorn", "services.inference_api:app", "--host", "0.0.0.0", "--port", "8000"]
