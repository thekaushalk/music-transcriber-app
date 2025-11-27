# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system packages required for FFmpeg and MuseScore
RUN apt-get update && \
    apt-get install -y ffmpeg musescore3 && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy requirements first (for caching builds)
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's source code
COPY . .

# Expose the port Flask runs on
EXPOSE 5000

# Set the environment variable for Flask
ENV FLASK_APP=app.py
ENV QT_QPA_PLATFORM=offscreen

# Start the Flask app
CMD ["flask", "run", "--host=0.0.0.0"]