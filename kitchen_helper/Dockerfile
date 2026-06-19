FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy sources
COPY ./kitchen_helper ./kitchen_helper

WORKDIR /app/kitchen_helper

# Install python deps
RUN pip install --no-cache-dir -U pip setuptools
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

EXPOSE 8000

ENV DB_PATH=/data/kitchen_helper.db
ENV HOMEASSISTANT_URL=http://supervisor/core/api

CMD ["/bin/sh", "./run.sh"]
