FROM python:3.11-slim

# Build-time argument with a default, then expose it as an environment variable
# at image runtime. This avoids BuildKit's "UndefinedVar" warning when the
# build-time variable isn't provided.
ARG XAI_MODE=legacy
ENV PYTHONUNBUFFERED=1
ENV XAI_MODE=$XAI_MODE

WORKDIR /app

# Install minimal build deps needed for some wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 5000

# Use gunicorn to run the Flask app; adjust module if you use `wsgi:app` or `run:app`
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "2"]
