# Use the official Python image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and change to the app directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install production dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy local code to the container image
COPY . .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Install and configure Functions Framework
ENV FUNCTION_TARGET=process_event
ENV FUNCTION_SIGNATURE_TYPE=event

# Run the web service on container startup using gunicorn
CMD exec functions-framework --target=${FUNCTION_TARGET} --signature-type=${FUNCTION_SIGNATURE_TYPE} --port=${PORT} 