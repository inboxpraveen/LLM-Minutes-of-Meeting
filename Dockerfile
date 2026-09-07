FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    MOM_DATA_DIR=/data

# ffmpeg converts recordings; curl backs the container health check.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set WITH_LOCAL_WHISPER=true to transcribe on this machine with no API key.
ARG WITH_LOCAL_WHISPER=false
COPY requirements.txt requirements-local.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$WITH_LOCAL_WHISPER" = "true" ]; then pip install --no-cache-dir -r requirements-local.txt; fi

COPY . .

RUN useradd --system --create-home --shell /usr/sbin/nologin app \
    && mkdir -p /data \
    && chown -R app:app /data /app
USER app

EXPOSE 5000

# The health check lives in docker-compose.yml: the worker and beat services are
# built from this same image and do not serve HTTP.

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "8", \
     "--timeout", "3600", "--keep-alive", "5", "--access-logfile", "-", "run:app"]
