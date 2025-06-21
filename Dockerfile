# Use official Python slim image
FROM python:3.10-slim

# Install system dependencies for espeak-ng and audio handling
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    espeak-ng \
    libespeak-ng1 \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all files to container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Flask will run on
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the Flask app
CMD ["python", "app.py"]
