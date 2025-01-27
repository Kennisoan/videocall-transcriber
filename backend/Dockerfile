# For production build
FROM python:3.10-slim AS prod

WORKDIR /app

# Copy requirements & install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src /app/src

# Expose port (FastAPI)
EXPOSE 8000

# Default command in production: run uvicorn without reload
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]