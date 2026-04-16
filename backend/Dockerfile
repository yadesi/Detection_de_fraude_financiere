FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-fixed.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/data/raw /app/data/processed /app/models /app/logs

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.main_simple:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
