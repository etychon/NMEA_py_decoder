# Dockerfile for NMEA Parser IOx Application
# Based on Python 3.9 Alpine for minimal size
FROM python:3.9-alpine

# Metadata
LABEL maintainer="NMEA Parser Team"
LABEL description="NMEA GPS/GNSS Data Parser for Cisco IOx"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers \
    && rm -rf /var/cache/apk/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY nmea_parser.py .
COPY splunk_config.py .
COPY splunk_logger.py .
COPY examples/ ./examples/
COPY sample_nmea.txt .

# Copy IOx-specific files
COPY iox_entrypoint.py .
COPY health_check.py .
COPY iox_config.py .

# Create logs directory
RUN mkdir -p /app/logs

# Create non-root user for security
RUN adduser -D -s /bin/sh nmea && \
    chown -R nmea:nmea /app
USER nmea

# Expose ports
EXPOSE 4001/udp
EXPOSE 8080/tcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 /app/health_check.py

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV NMEA_UDP_PORT=4001
ENV NMEA_MODE=udp
ENV NMEA_CONTINUOUS=true
ENV NMEA_LOG_LEVEL=INFO

# Entry point
CMD ["python3", "iox_entrypoint.py"]
