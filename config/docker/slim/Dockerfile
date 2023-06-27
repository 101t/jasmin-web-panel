FROM python:3.11-slim

# disable debian interactive
ARG DEBIAN_FRONTEND=noninteractive
# suppress pip upgrade warning
ARG PIP_DISABLE_PIP_VERSION_CHECK=1
# disable cache directory, image size 2.1GB to 1.9GB
ARG PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get -y upgrade

RUN apt-get install --no-install-recommends -y  \
    python3-dev python3-wheel python3-setuptools virtualenv \
    build-essential gcc curl \
    libpq-dev libpq5 telnet

# Pillow dependencies
RUN apt-get install  --no-install-recommends -y \
    libtiff5-dev libjpeg-dev libopenjp2-7-dev zlib1g-dev  \
    libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev  \
    tk8.6-dev python3-tk libharfbuzz-dev libfribidi-dev libxcb1-dev

RUN apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

# --------------------------------------
ENV APP_DIR=/app
ENV APP_USER=app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1

RUN useradd -m -d ${APP_DIR} -U -r -s /bin/bash ${APP_USER}

USER ${APP_USER}

WORKDIR ${APP_DIR}

# Create the virtual environment
RUN python -m venv /app/env
# Activate the virtual environment
ENV PATH="$APP_DIR/env/bin:$PATH"

COPY scripts/base.txt base.txt
COPY scripts/production.txt requirements.txt

RUN pip install -U pip wheel

RUN pip install -r requirements.txt

# copy code to image
COPY --chown=$APP_USER . .

COPY --chown=$APP_USER config/docker/docker-entrypoint.sh docker-entrypoint.sh

RUN mkdir -p public/static && mkdir -p public/media && mkdir -p logs/

EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]

HEALTHCHECK --interval=10s --timeout=10s --retries=30 \
    CMD curl -L http://127.0.0.1:8000/api/health_check > /dev/null

