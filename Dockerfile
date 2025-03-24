# Use Python 3.10 as the base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt update && apt install -y build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the Django application code
COPY . /app/

# Run migrations before starting the app
RUN python manage.py migrate

# Expose the port dynamically
ARG PORT=8000
ENV PORT=${PORT}
EXPOSE ${PORT}

# Start the application using Gunicorn with the specified port
CMD ["sh", "-c", "gunicorn moneytransfer.wsgi:application --bind 0.0.0.0:5000"]