FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set the Python path to include the app directory
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Create directories for mounted volumes
RUN mkdir -p /app/src /app/utils /app/modeling/artifacts

# Create a simple main.py file that directly imports from app.py
RUN echo 'import sys\n\
sys.path.insert(0, "/app")\n\
import importlib.util\n\
spec = importlib.util.spec_from_file_location("app_module", "/app/src/app.py")\n\
app_module = importlib.util.module_from_spec(spec)\n\
spec.loader.exec_module(app_module)\n\
app = app_module.app' > /app/main.py

# Copy model artifacts and data
COPY data/processed /app/data/processed

# Copy and set entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Command to run the application
ENTRYPOINT ["/app/entrypoint.sh"] 