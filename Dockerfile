FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY apps/ ./apps/

# Expose API port
EXPOSE 8000

# Run FastAPI server
CMD ["python", "-m", "uvicorn", "src.extension.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
