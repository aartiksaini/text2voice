# Use lightweight Python base
FROM python:3.11-slim

# Install espeak-ng and other dependencies
RUN apt update && apt install -y espeak-ng ffmpeg && apt clean

# Set working directory
WORKDIR /app

# Copy your code
COPY . .

# Install Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Allow port (Railway uses dynamic port, so we’ll read from env)
EXPOSE 8000

# Start the app
CMD ["python", "app.py"]
